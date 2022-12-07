import logging

from columbine.soap import dict_to_xml
from .base import ColumbineBaseFlow

logger = logging.getLogger("django_columbine.%s" % __name__)


class COAXOrderFlow(ColumbineBaseFlow):
    name = "order"
    servicename = "newCoaxBitStreamAccess"
    require_validate = True
    require_acknowledge = True

    def get_xml_body(self, tx):
        if tx.stage == "validate":
            # add empty parameter-list
            root = self.element(
                "parameter-list", self.element("installation", self.element("address"))
            )

            # add our kwargs to the address element
            for xmlement in dict_to_xml(tx.flow.kwargs):
                root.find("installation").find("address").append(xmlement)
            # add service name to parameterlist
            root.append(self.element("service", "BSAC-OPR"))

            # go
            return root
        if not tx.flow.orders.exists():
            logger.error("No order found for %s" % tx.flow)
            return False

        logger.error("later stages not implemented")
        return False

    def handle_reply(self, tx):
        """
        Whatever will we do here
        """
        return True


class FBSAOrderFlow(ColumbineBaseFlow):
    name = "order"
    servicename = "newFiberEthernetBitStreamAccess"
    require_validate = True
    require_acknowledge = True

    def get_xml_body(self, tx):
        # add empty parameter-list
        root = self.element(
            "parameter-list", self.element("installation", self.element("address"))
        )

        # add our kwargs to the address element
        for xmlement in dict_to_xml(tx.flow.kwargs):
            root.find("installation").find("address").append(xmlement)
        # add service name to parameterlist
        root.append(self.element("service", "BSAEF-OPR-U-LID"))

        if tx.stage == "validate":
            # nothing else needed, go
            return root

        if tx.stage == "order":
            # add order object including product list
            return root

    def handle_reply(self, tx):
        """
        Whatever will we do here
        """
        return True


class VULAOrderFlow(ColumbineBaseFlow):
    name = "order"
    servicename = "newVulaEthernetBitStreamAccess"
    require_validate = True
    require_acknowledge = True

    def get_xml_body(self, tx):
        if tx.stage == "validate":
            # add empty parameter-list
            root = self.element(
                "parameter-list", self.element("installation", self.element("address"))
            )

            # add our kwargs to the address element
            for xmlement in dict_to_xml(tx.flow.kwargs):
                root.find("installation").find("address").append(xmlement)
            # add service name to parameterlist
            root.append(self.element("service", "VULA-OPR-U-LID"))

        # go
        return root

    def handle_reply(self, tx):
        """
        Whatever will we do here
        """
        return True


class OrderCancelFlow(ColumbineBaseFlow):
    name = "cancel-order"
    require_validate = True
    require_acknowledge = True
