#!/usr/bin/env python3
# pylint: disable=W,C

from setuptools import setup, find_packages
setup(
    name = "psvpack",
    version = "0.1.0",
    author = "Jacob Hipps",
    author_email = "jacob@ycnrg.org",
    license = "MIT",
    description = "PS Vita pkg fetch tool",
    keywords = "psvita psv vita pkg2zip",
    url = "https://git.ycnrg.org/projects/HBREW/psvpack",

    packages = find_packages(),
    scripts = [],

    install_requires = ['docutils', 'requests', 'arrow>=0.7.0', 'progressbar2', 'pyyaml'],

    package_data = {
        '': [ '*.md' ],
    },

    entry_points = {
        'console_scripts': [ 'psvpack = psvpack.cli:_main' ]
    }

    # could also include long_description, download_url, classifiers, etc.
)
