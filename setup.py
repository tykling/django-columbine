import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="django-columbine",
    version="0.6.0",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    license="BSD License",
    description="A Django implementation of the Danish ISP TDCs provisioning system Columbine.",
    long_description=README,
    url="https://github.com/tykling/django-columbine",
    author="Thomas Steen Rasmussen",
    author_email="thomas@gibfest.dk",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    install_requires=["zeep", "asn1", "xmlschema", "pyyaml", "xmltodict", "pyOpenSSL"],
)
