"""A cross-platform launcher for film and games projects, built on Rez"""

import os
from setuptools import setup, find_packages
from launchapp2.version import version

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
fname = os.path.join(dirname, "launchapp2", "__version__.py")
with open(fname, "w") as f:
    f.write("version = \"%s\"\n" % version)

setup(
    name="launchapp2",
    version=version,
    description=(
        "A cross-platform launcher for film and games built on Rez"
    ),
    keywords="launcher package resolve version software management",
    long_description=__doc__,
    url="https://github.com/mottosso/launchapp2",
    author="Marcus Ottosson",
    author_email="konstruktion@gmail.com",
    license="LGPL",
    zip_safe=False,
    packages=find_packages(),
    package_data={
        "launchapp2": [
            "resources/*.png",
            "resources/*.css",
        ]
    },
    entry_points={
        "console_scripts": [
            "launchapp2 = launchapp2",
            "la2 = launchapp2",
        ]
    },
    classifiers=classifiers,
    install_requires=[
    ],
    python_requires=">2.7, <4",
)
