import inspect
import logging

from columbine.soap import dict_to_xml, rename_dict_keys
from .base import ColumbineBaseFlow

logger = logging.getLogger("django_columbine.%s" % __name__)


class ShowNetInfoFlow(ColumbineBaseFlow):
    """
    Flow class to search ShowNetInfo.
    Used directly by ShowNetInfoClient.lid() and subclassed by
    the other ShowNetInfo* flows.
    """

    name = "show-net-info"
    servicename = "showNetInfo"
    reply_element_name = "circuit-list"

    def handle_reply(self, tx):
        """
        Figure out what the lid() call returns before we know what to
        do with the reply. We have no test data to make the call now.
        """
        return True


class ShowNetInfoAddressFlow(ShowNetInfoFlow):
    """
    Flow class to search ShowNetInfo for an address
    """

    def get_xml_body(self, transaction):
        # add empty parameter-list
        root = self.element(
            "parameter-list", self.element("installation", self.element("address"))
        )
        # add our kwargs to the address element
        for xmlement in dict_to_xml(transaction.flow.kwargs):
            if xmlement.tag == "visitationNodeAnalysisSeq":
                # skip this one, ShowNetInfoVNASFlow will add it
                continue
            root.find("installation").find("address").append(xmlement)

        # for address searches we need to add equipment-type=ALL
        # inside <netinfo-parameters>
        root.append(
            self.element("netinfo-parameters", self.element("equipment-type", "ALL"))
        )

        return root

    def handle_reply(self, tx):
        """
        Find all <circuit-list-item> elements and create a new
        ShowNetInfoVNASFlow for each of them.
        """
        # loop over circuit-list and create a flow for each circuit
        circuitlist = tx.reply_json["reply"]["circuit_list"]["circuit_list_item"]
        for circuit in circuitlist:
            # create message and log it
            message = (
                "Creating new ShowNetInfoVNASFlow for visitationNodeAnalysisSeq %s"
                % circuit["visitationNodeAnalysisSeq"]
            )
            logger.info(message)

            # start building kwargs, add VNAS from the circuit
            kwargs = {}
            kwargs["vnas"] = circuit["visitationNodeAnalysisSeq"]

            # add address elements from the original search to kwargs
            address = tx.request_json["command"]["parameter-list"]["installation"][
                "address"
            ]
            address = rename_dict_keys(address)

            kwargs.update(address)

            # import Client and create Flow
            from columbine.clients import ShowNetInfoClient

            newflow = ShowNetInfoClient(
                reason=message,
                source=self.get_source(
                    line=inspect.getframeinfo(inspect.currentframe()).lineno
                ),
                parent_flow=tx.flow,
                references=tx.flow.references,
            ).visitation_node_analysis_seq(**kwargs)
            logger.info("created new ShowNetInfoVNAS flow %s" % newflow)

        # all good
        return True


class ShowNetInfoVNASFlow(ShowNetInfoAddressFlow):
    """
    Flow class to search ShowNetInfo for a VNAS (which must also
    include a unique address).
    """

    reply_element_name = "circuit-data"

    def get_xml_body(self, transaction):
        """
        Add <visitationNodeAnalysisSeq> to the XML
        """
        # get xml body with the <installation><address> structure
        root = super().get_xml_body(transaction)
        # add <visitationNodeAnalysisSeq> to <parameter-list>
        root.append(
            self.element(
                "visitationNodeAnalysisSeq",
                transaction.flow.kwargs["visitationNodeAnalysisSeq"],
            )
        )
        # remove netinfo-parameters
        root.remove(root.find("netinfo-parameters"))

        return root

    def handle_reply(self, tx):
        """ Create VNAS object with the data """
        vnas_data = tx.reply_json["reply"]["circuit_data"]
        from columbine.models import VNAS

        vnas = VNAS.objects.create(
            flow=tx.flow, data=vnas_data, references=tx.flow.references
        )
        logger.info("Created new %s" % vnas)
