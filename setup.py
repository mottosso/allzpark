"""A cross-platform launcher for film and games projects, built on Rez"""

import os
from setuptools import setup, find_packages
from allspark.version import version

# Git is required for deployment
assert len(version.split(".")) == 3, (
    "Could not compute patch version, see version.py")

classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Topic :: Utilities"
    "Topic :: Software Development",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

# Store version alongside package
dirname = os.path.dirname(__file__)
fname = os.path.join(dirname, "allspark", "__version__.py")
with open(fname, "w") as f:
    f.write("version = \"%s\"\n" % version)

setup(
    name="allspark",
    version=version,
    description=__doc__,
    keywords="launcher package resolve version software management",
    long_description=__doc__,
    url="https://github.com/mottosso/allspark",
    author="Marcus Ottosson",
    author_email="konstruktion@gmail.com",
    license="LGPL",
    zip_safe=False,
    packages=find_packages(),
    package_data={
        "allspark": [
            "resources/*.png",
            "resources/*.css",
        ]
    },
    classifiers=classifiers,
    install_requires=[
    ],
    python_requires=">2.7, <4",
)
