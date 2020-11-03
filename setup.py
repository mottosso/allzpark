"""A cross-platform launcher for film and games projects, built on Rez"""

import os
from setuptools import setup, find_packages
from allzpark.version import version

# Git is required for deployment
assert len(version.split(".")) == 3, (
    "Could not compute patch version, make sure `git` is\n"
    "available and see version.py for details")

classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Topic :: Utilities",
    "Topic :: Software Development",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

# Store version alongside package
dirname = os.path.dirname(__file__)
fname = os.path.join(dirname, "allzpark", "__version__.py")
with open(fname, "w") as f:
    f.write("version = \"%s\"\n" % version)

setup(
    name="allzpark",
    version=version,
    description=__doc__,
    keywords="launcher package resolve version software management",
    long_description=__doc__,
    url="https://github.com/mottosso/allzpark",
    author="Marcus Ottosson",
    author_email="konstruktion@gmail.com",
    license="LGPL",
    zip_safe=False,
    packages=find_packages(),
    package_data={
        "allzpark": [
            "resources/*.png",
            "resources/*.css",
            "resources/*.svg",
            "resources/fonts/*/*.ttf",
        ]
    },
    entry_points={
        "console_scripts": [
            "allzpark = allzpark.cli:main",

            # Alias
            "azp = allzpark.cli:main",
        ]
    },
    classifiers=classifiers,
    install_requires=[
        "bleeding-rez>=2.38.2",
        "allzparkdemo>=1",

        # Specifically for Python 2..
        "PySide; python_version<'3'",

        # ..and likewise for Python 3
        "PySide2; python_version>'3'",
    ],
    python_requires=">2.7, <4",
)
