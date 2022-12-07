import logging
import xmlschema

from .conf import columbine_settings

logger = logging.getLogger("django_columbine.%s" % __name__)


def validate_xml(xsdpath, xmlement):
    """
    Validate the XML with the schema, return True or False

    Args:
        xsd (str): The path to the XSD file
        xmlement (lxml.etree.ElementTree): The XML to be validated

    Returns:
        bool: The return value. True for valid, false for invalid.
    """
    schema = xmlschema.XMLSchema(xsdpath)
    # logger.debug("Loaded schema from path %s: %s" % (xsdpath, schema))
    # logger.debug("Validating XML: %s" % etree.tostring(xmlement))
    valid = schema.is_valid(xmlement)
    # raise exception?
    # schema.validate(etree.tostring(xmlement).decode('utf-8'))
    if not valid:
        logger.warning("Element is not valid")
    else:
        logger.warning("Element is valid")
    return valid


def validate_command_xml(xmlement):
    """
    Validate XML with the columbine_settings.XSD_COMMAND schema file

    Args:
        xmlement (lxml.etree.ElementTree): The XML to be validated

    Returns:
        bool: The return value. True for valid, false for invalid.
    """
    return validate_xml(xsdpath=columbine_settings.XSD_COMMAND, xmlement=xmlement)


def validate_reply_xml(xmlement):
    """
    Validate XML with the columbine_settings.XSD_REPLY schema file

    Args:
        xmlement (lxml.etree.ElementTree): The XML to be validated

    Returns:
        bool: The return value. True for valid, false for invalid.
    """
    return validate_xml(xsdpath=columbine_settings.XSD_REPLY, xmlement=xmlement)
