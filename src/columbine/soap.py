import logging
import json
from zeep import Client
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from requests import Session
from lxml import objectify
import xmltodict

from .conf import columbine_settings

logger = logging.getLogger("django_columbine.%s" % __name__)


def get_soap_client():
    """
    Return a zeep.Client object ready to speak SOAP with the Columbine API, or False if an exception happens.
    """
    try:
        session = Session()
        session.cert = (
            columbine_settings.COLUMBINE_CLIENT_CERT,
            columbine_settings.COLUMBINE_CLIENT_KEY,
        )
        transport = Transport(session=session)
        history = HistoryPlugin()
        client = Client(
            columbine_settings.COLUMBINE_URL, transport=transport, plugins=[history]
        )
        return client, history
    except Exception:
        logger.exception("Unable to initialise soap client")
        return False, None


def dict_to_xml(data, E=None, depth=0):
    """
    Recursive function to convert a dict to a tuple of lxml.objectify
    XML elements, suitable for looping over and .append()'ing to
    another XML element.

    Running this in a shell:
        for xmlement in dict_to_xml(
        {
            'a': 1,
            'b': {
                'c': 2,
                'd': 3
            },
            'e': 4
        }):
            print(etree.tostring(xmlement))

    Would return:
        b'<e>4</e>'
        b'<a>1</a>'
        b'<b><c>2</c><d>3</d></b>'

    Args:
        data (dict): The dict of data to return as XML
        E (lxml.objectify.ElementMaker): An instance of ElementMaker to
        use. We pass it on when calling recursively so we only need to
        instantiate it once.
        depth (int): The depth of recursion, may be used for debugging
        messages.

    Returns:
        tuple of lxml.objectify.ObjectifiedElement instances
    """
    # logger.debug("    " * depth + "Inside dict_to_xml with data %s" % data)
    if not E:
        # we must be at depth=0, so we need an ElementMaker!
        E = objectify.ElementMaker(annotate=False)

    if not isinstance(data, dict):
        logger.error(
            "dict_to_xml() must be called with a dict as the data argument! (hence the name)"
        )
        raise ValueError

    # get an empty tuple we can add elements to
    elements = ()

    # loop over elements in the data dict
    for key, value in data.items():
        if isinstance(value, dict):
            # Value is a dict, call recursively and add the resulting
            # elements. We have to use getattr() because some elements
            # have dashes in them :/ Remember the trailing comma
            # because we are adding this to a tuple!
            elements += (
                getattr(E, key)(*dict_to_xml(data=value, E=E, depth=depth + 1)),
            )
        else:
            # value is not a dict, just add it as is
            # we have to use getattr() because some elements have
            # dashes in them :/ Remember the trailing comma because
            # we are adding this to a tuple
            elements += (getattr(E, key)(value),)

    return elements


def dict_to_root_xml(name, data, E=None, depth=0):
    """
    Recursive function to convert a dict to an lxml.objectify XML
    element with the specified name.

    Args:
        name (str): The name of the root XML element to return
        data (dict): The dict of data to return as XML
        E (lxml.objectify.ElementMaker): An instance of ElementMaker to
        use. We pass it when calling recursively so we only need to
        instantiate it once.
        depth (int): The depth of recursion, may be used for debugging
        messages.

    Returns:
        lxml.objectify.ObjectifiedElement
    """
    # logger.debug("   " * depth + "Inside dict_to_root_xml with name %s and data %s" % (name, data))

    # we must be at depth=0, so we need an ElementMaker!
    if not E:
        # logger.debug("Creating new ElementMaker...")
        E = objectify.ElementMaker(annotate=False)
        # logger.debug("Created ElementMaker %s" % E)

    # data must be a dict
    if not isinstance(data, dict):
        logger.error(
            "dict_to_root_xml() must be called with a dict as the data argument!"
        )
        raise ValueError

    # get a new empty XML element with the requested name
    xml = getattr(E, name)()

    # loop over elements in the data dict
    for key, value in data.items():
        if isinstance(value, dict):
            # value is a dict, call recursively and return the resulting element
            xml.append(dict_to_root_xml(data=value, name=key, E=E, depth=depth + 1))
        else:
            # value is not a dict, just add it
            # we have to use getattr() because some elements have dashes in them :/
            xml.append(getattr(E, key)(value))
    # logger.debug("returning xml: %s" % tostring(xml))
    return xml


def xml_to_json(self, xml):
    """
    Parse the XML and transform it to JSON
    Takes XML as a string and parses with xmltodict.parse()
    Returns JSON as a string.
    """
    if not xml:
        return False
    return json.dumps(xmltodict.parse(xml, dict_constructor=dict))


def rename_dict_keys(data, find="-", replace="_"):
    """
    Recursive method to find and replace something in dict keys.
    Useful for replacing dashes with underscores in dicts created
    from XML responses full of dashes in the element names.
    """
    if isinstance(data, dict):
        # data is a dict or dict derived type, call recursively
        result = data.__class__()
        for key, value in data.items():
            key = key.replace(find, replace)
            result[key] = rename_dict_keys(value, find, replace)
    elif isinstance(data, (list, set, tuple)):
        # this is a list or similar, use comprehension and recurse
        result = data.__class__(
            rename_dict_keys(element, find, replace) for element in data
        )
    else:
        # must be string, int, or float, just return it
        return data
    return result
