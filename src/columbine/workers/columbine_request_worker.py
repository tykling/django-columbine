import logging
from lxml import etree
import xmltodict

from django.db import transaction

from columbine.models import Flow, Request
from columbine.soap import get_soap_client, rename_dict_keys
from columbine.pkcs7 import pkcs7_encode, pkcs7_decode
from columbine.xsd import validate_reply_xml
import columbine.flows

logger = logging.getLogger("django_columbine.%s" % __name__)


def do_work():
    """
    The request worker picks a Flow which has a Transaction without an
    associated Request object. When a transaction has been picked the
    "attempts" counter is increased and we start making the request. If
    an error with the Transaction is encountered we put it in the error
    field. We do not touch the tx.result bool here, it will be set later
    based on tx.error being empty or not.
    """
    # we manage the transaction manually, otherwise the first tx.save()
    # will release the lock, which is not what we want
    with transaction.atomic():
        # first try to get a flow we haven't tried before
        flow = (
            Flow.objects.select_for_update(skip_locked=True, of=("self",))
            .filter(
                # get unfinished Flows
                finished=False,
                # with one or more Transactions
                transactions__isnull=False,
                # where at least one has no Request
                transactions__request__isnull=True,
                # and where we haven't tried before
                transactions__attempts=0,
            )
            .first()
        )

        if not flow:
            # logger.info("No flows with 0 attempts, retrying a flow we've tried before...")
            # then try to get a flow we have tried before
            flow = (
                Flow.objects.select_for_update(skip_locked=True, of=("self",))
                .filter(
                    # get unfinished Flows
                    finished=False,
                    # with one or more Transactions
                    transactions__isnull=False,
                    # where at least one has no Request
                    transactions__request__isnull=True,
                    # and where we haven't tried before
                    transactions__attempts__gt=0,
                )
                .order_by(
                    # order by modified_date so we try the one which has "waited the longest",
                    # this should ensure that we always re-try all the failing transations in order.
                    "modified_date"
                )
                .first()
            )
            if not flow:
                # logger.error("No Transactions to handle right now")
                return

        # we have a flow
        logger.debug("Picked %s with %s attempts" % (flow, flow.attempts))

        # get the first transaction without an associated Request
        tx = flow.transactions.filter(request__isnull=True).first()
        logger.info(
            "Processing Transaction %s - %s attempts before this one"
            % (tx.tag, tx.attempts)
        )

        # increase attempts counter (no need to use F() - we have a lock)
        tx.attempts += 1
        tx.save()

        # import the flowclass
        try:
            flowclass = getattr(columbine.flows, tx.flow.name)()
        except ValueError:
            message = "Tx %s flow class %s not found in columbine.flows" % (
                tx,
                tx.flow.name,
            )
            logger.error(message)
            # this flow is unlikely to succeed in the future,
            # register error so we dont retry
            tx.error = message
            tx.save()
            return

        # get the soap client
        client, history = get_soap_client()
        if not client:
            logger.error(
                "Unable to get SOAP client, bailing out, will retry %s later" % tx
            )
            return

        logger.debug(
            "SOAP service object has the following methods: %s" % dir(client.service)
        )
        # sign and pkcs#7 encode the xml
        logger.debug("Signing XML payload...")
        xmlbytes = tx.request_xml.encode("iso8859-1")
        signed = pkcs7_encode(xmlbytes)
        if not signed:
            logger.error(
                "No signed payload returned from pkcs7_encode(), bailing out, will retry %s later"
                % tx
            )
            return

        # get the SOAP service object from zeep
        logger.debug(
            "Getting SOAP service object for service %s" % flowclass.servicename
        )
        try:
            service = getattr(client.service, flowclass.servicename)
        except Exception:
            logger.exception(
                "Unable to get the SOAP service object, bailing out, will retry %s later"
                % tx
            )
            return

        # call the service
        try:
            logger.debug("Calling SOAP service...")
            response = service(arg0=signed)
            logger.debug(
                "Received %s bytes reply from service %s"
                % (len(response), flowclass.servicename)
            )
        except Exception:
            logger.exception(
                "Got exception while calling SOAP service, baling out, will retry %s later"
                % tx
            )
            return

        # create a Request object to save this request
        req = Request.objects.create(
            transaction=tx,
            request_headers=history.last_sent["http_headers"],
            request_body=etree.tostring(history.last_sent["envelope"]).decode(
                "iso8859-1"
            ),
            response_status_code=200,  # TODO: how to get this?!
            response_headers=dict(history.last_received["http_headers"]),
            response_body=etree.tostring(history.last_received["envelope"]).decode(
                "iso8859-1"
            ),
        )
        logger.debug("Saved new request in database as %s" % req)

        # PKCS#7 decode the response, returns payload as a string
        logger.debug("Parsing response...")
        payload_bytes = pkcs7_decode(response)
        if not payload_bytes:
            logger.error("No response payload received, bailing out")
            return
        logger.debug("Got %s bytes response payload" % len(payload_bytes))

        # parse the XML
        xmlement = etree.fromstring(payload_bytes)

        # decode the payload
        payload = payload_bytes.decode("iso8859-1")

        # save reply XML (as json, with dashes replaced with underscore)
        tx.reply_json = rename_dict_keys(
            xmltodict.parse(payload, dict_constructor=dict)
        )

        # save columbine session ID where needed
        if not tx.flow.columbine_session_id:
            logger.debug("Saving Columbine session ID...")
            try:
                tx.flow.columbine_session_id = (
                    xmlement.find("cb-system").find("columbine-session-id").text
                )
                tx.flow.save()
            except AttributeError:
                logger.error("No Columbine session ID found in XML :(")

        # validate reply XML payload syntax with our XSDs
        logger.debug("Validating reply XML...")
        tx.reply_xml_valid = validate_reply_xml(xmlement)

        # did this tx result in an XML error? look for the <error>
        # element just below the root <reply> element
        if "error" in tx.reply_json["reply"]:
            tx.error = tx.reply_json["reply"]["error"]
        else:
            # no error reported from Columbine, check xml element
            # name sanity
            if not flowclass.validate_reply(tx, xmlement):
                tx.error = {
                    "django-columbine-error": "flowclass.validate_reply() returned False"
                }

        # Save the transaction, the rest of the reply handling will
        # be done by columbine_flow_processor.
        tx.save()

        logger.debug("Done.")
