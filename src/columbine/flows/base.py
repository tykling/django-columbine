import logging
from lxml import objectify

from columbine.conf import columbine_settings
from columbine.soap import dict_to_xml

logger = logging.getLogger("django_columbine.%s" % __name__)


class ColumbineBaseFlow:
    """
    All Columbine Flow classes inherit from this class
    Child classes must set "name" and "servicename" and maybe
    override get_xml_body() if anything special is needed.
    """

    # set True if the Flow needs to start with a -validate Transaction
    require_validate = False

    # set True if the Flow needs to end with a -ack Transaction
    require_acknowledge = False

    # override these XSD paths used for XML validation as needed
    command_xsd = columbine_settings.XSD_COMMAND
    reply_xsd = columbine_settings.XSD_REPLY

    # initialize the ElementMaker so we can use self.E()
    E = objectify.ElementMaker(annotate=False)

    def element(self, name, *args):
        """
        Return an element with the supplied name and payload. Expects
        self.E to be an instance of lxml.objectify.ElementMaker()

        Args:
            name (str): The name of the XML element to return
            *args: A tuple of string or XML elements to include as contents of the returned element

        Returns:
            lxml.objectify.ObjectifiedElement
        """
        return getattr(self.E, name)(*args)

    @property
    def transaction_count(self):
        """all flows have at least one transaction"""
        count = 1
        if self.require_validate:
            count += 1
        if self.require_acknowledge:
            count += 1
        return count

    def get_xml_body(self, transaction):
        """
        Generate and return XML based on transaction.kwargs data

        Args:
            transaction (columbine.models.Transaction): The Transaction we are working with

        Returns:
            lxml.etree.ElementTree: The finished XML element
        """
        # add empty parameter-list
        root = self.element("parameter-list")

        # add our kwargs (if we have any)
        if transaction.flow.kwargs:
            for xmlement in dict_to_xml(transaction.flow.kwargs):
                root.append(xmlement)

        return root

    def validate_reply(self, tx, xmlement):
        """
        Do basic validation to check that the reply is as expected.
        This includes checking the flow name and reply xml element name.
        Returns True if all is well, False otherwise.
        """
        # do we have the expected flow name?
        name = xmlement.find("name").text
        if name != self.get_tx_name(stage=tx.stage):
            message = "Wrong flow name encountered, expected '%s', found '%s'" % (
                self.get_tx_name(tx.stage),
                name,
            )
            logger.error(message)
            tx.error = message
            return False

        if tx.stage == "order":
            # do we have a reply body with the expected xml element name?
            body = xmlement.find(self.reply_element_name)
            if body is None:
                message = "No %s element found, bailing out" % self.reply_element_name
                logger.error(message)
                tx.error = message
                return False

        # all good
        return True

    def handle_reply(self, tx):
        """
        This method must be implemented in each flow to handle parsing
        of the reply. Must return True if reply handling went well, or
        False if an error was encountered.
        """
        raise NotImplementedError

    def get_tx_name(self, stage):
        """ Transaction name depends on stage """
        if stage == "validate":
            return self.name + "-validate"
        elif stage == "ack":
            return self.name + "-ack"
        else:
            return self.name

    def get_source(self, line, method="handle_reply()"):
        """
        Convenience method to return a string with the source.
        Used by Flow classes when creating new Flows.
        """
        return "%s.%s line %s" % (self.__class__.__name__, method, line)
