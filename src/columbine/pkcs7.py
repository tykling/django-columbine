import logging
import subprocess
import base64

from asn1crypto import cms
from OpenSSL.crypto import (
    load_certificate,
    dump_certificate,
    FILETYPE_ASN1,
    FILETYPE_PEM,
    verify,
)
from columbine.conf import columbine_settings

logger = logging.getLogger("django_columbine.%s" % __name__)


def pkcs7_encode(xmlbytes, encoding="iso8859-1"):
    """
    For now this just uses commandline openssl to build the object.
    TODO: Figure out how to encode a PKCS#7 object in python
    """
    return pkcs7_encode_openssl(xmlbytes, encoding)


def pkcs7_encode_openssl(xmlbytes, encoding="iso8859-1", keypath=None, certpath=None):
    """
    Use commandline openssl to encode bytes as a signed and base64 encoded PKCS#7 object.
    """
    # default to paths from settings
    if not keypath:
        keypath = columbine_settings.COLUMBINE_CLIENT_KEY
    if not certpath:
        certpath = columbine_settings.COLUMBINE_CLIENT_CERT

    # put the openssl commandline together
    command = "openssl cms -sign -signer %s -inkey %s -nodetach -outform pem" % (
        certpath,
        keypath,
    )

    # run the openssl command
    p = subprocess.run(command.split(" "), stdout=subprocess.PIPE, input=xmlbytes)

    # decode the output
    output = p.stdout.decode(encoding).strip()
    if not output:
        logger.error("No output from openssl command :(")
        return False

    # split by line
    lines = output.split("\n")

    # remove first and last lines (----BEGIN--- and ---END---)
    lines = lines[1:-1]

    # make a multiline string out of the remaining lines and return
    pem = "\n".join(lines)
    return pem


def pkcs7_decode(base64_string, encoding="iso8859-1"):
    """
    Takes a base64 encoded PKCS#7 asn.1 object as input,
    returns a tuple of (payload, signing_result) where payload
    is the signed data, and signing_result is a bool which is True
    if the signature was verified with columbine_settings.TRUSTED_PKCS7_CERT
    """
    # parse the outermost ContentInfo object (after base64 encoding)
    contentinfo = cms.ContentInfo.load(base64.b64decode(base64_string))

    # check content_type
    if contentinfo["content_type"].native != "signed_data":
        logger.error(
            "Expected 'content_type' of %s to be 'signed_data' but it is %s - bailing out"
            % (contentinfo, contentinfo["content_type"])
        )
        return None, False

    # get payload
    payload_bytes = contentinfo["content"]["encap_content_info"]["content"].native

    # get certificates included in the PKCS#7
    certificates = contentinfo["content"]["certificates"]
    signing_cert_data = certificates[0].chosen.dump()
    signing_cert = load_certificate(FILETYPE_ASN1, signing_cert_data)
    logger.debug("signing cert is: %s" % signing_cert.get_subject())

    # read trusted certificate from disk
    with open(columbine_settings.TRUSTED_PKCS7_CERT, "r") as f:
        trusted_cert = load_certificate(FILETYPE_PEM, f.read())
    logger.debug("trusted cert is: %s" % trusted_cert.get_subject())

    # compare signing and trusted certificate
    if dump_certificate(FILETYPE_PEM, signing_cert) != dump_certificate(
        FILETYPE_PEM, trusted_cert
    ):
        logger.error(
            "Message is signed with the wrong certificate %s - we expected %s"
            % (signing_cert.get_subject(), trusted_cert.get_subject())
        )
        return None, False

    # TODO: verify signature using python
    # get signature
    # signer_info = contentinfo['content']['signer_infos'][0]
    # result = pkcs7_signature_verify_python(
    #    trusted_cert_path=columbine_settings.TRUSTED_PKCS7_CERT,
    #    signature=signer_info['signature'].native,
    #    data=payload_bytes,
    #    digest=signer_info['digest_algorithm']['algorithm'].native,
    # )

    # verify signature using commandline openssl
    result = pkcs7_signature_verify_openssl(
        trusted_cert_path=columbine_settings.TRUSTED_PKCS7_CERT, data=base64_string
    )

    # check result, log message and return
    if result:
        logger.debug(
            "Signature verify OK, returning %s bytes payload..." % len(payload_bytes)
        )
        return payload_bytes
    else:
        logger.error("Signature verify FAIL, returning False...")
        return False


def pkcs7_signature_verify_openssl(trusted_cert_path, data):
    """
    Use commandline OpenSSL to verify signature validity
    """
    logger.debug("Running openssl...")
    command = (
        "openssl cms -inform pem -verify -nointern -certfile %s -noverify"
        % trusted_cert_path
    )

    # run the openssl command
    p = subprocess.run(
        command.split(" "),
        stdout=subprocess.PIPE,
        input=cms_ascii_armor(data).encode("iso8859-1"),
    )

    if p.returncode == 0:
        logger.debug("The signature is valid.")
        return True
    else:
        logger.error(
            "The signature is not valid. Error: %s"
            % p.stderr.decode("iso8859-1").strip()
        )
        return False


def pkcs7_signature_verify_python(trusted_cert_path, signature, data, digest):
    """
    Use OpenSSL.crypto.verify() to verify signature validity
    """
    # read the certificate
    with open(trusted_cert_path, "r") as f:
        trusted_cert = load_certificate(FILETYPE_PEM, f.read())

    # verify the signature
    try:
        verify(cert=trusted_cert, signature=signature, data=data, digest=digest)
        logger.debug("The signature is valid.")
        result = True
    except Exception as e:
        logger.error("The signature is not valid. Exception: %s" % e)
        result = False
    return result


def cms_ascii_armor(data):
    """
    Wrap data in "-----BEGIN CMS-----" and "-----END CMS-----" lines
    """
    output = "-----BEGIN CMS-----\n"
    output += data
    output += "\n-----END CMS-----"
    return output
