#!/usr/bin/env python3
# vim: set ts=4 sw=4 expandtab syntax=python:
"""

psvpack.cli
Digital capture & processing helper
CLI entry-point

@author   Jacob Hipps <jacob@ycnrg.org>

Copyright (c) 2018 J. Hipps / Neo-Retro Group, Inc.
https://ycnrg.org/

"""

__version__ = '0.1.0'
__date__ = '06 Aug 2018'

default_config = {
    'cache_dir': "~/.config/psvpack",
    'cache_ttl': 86400,
    'pkg2zip': "/usr/local/bin/pkg2zip",
    'tsv_urls': {
        'PSV': "",
        'PSM': "",
        'PSX': "",
        'PSP': "",
        'PSV_DLC': "",
        'PSP_DLC': "",
    },
    'install_root': "./"
}

conf_header = """\
# psvpack - user configuration file
#
# To revert back to defaults, simply delete this file, and it will be recreated
# the next time psvpack is run.
#
# Be sure to set the following values correctly:
# * pkg2zip  - Path to the pkg2zip binary (if you're unsure, run `which pkg2zip`)
# * tsv_urls - TSV update URLs (should be obtained independently); required for operation
#
# Optional:
# * install_root - can be set to the correct path to have psvpack automatically
#                  install packages to your Vita while it's plugged in
#                  (for example, it might be auto-mounted to `/media/USER/xxxxx`).
#                  By default, the current directory is used.
# * cache_dir    - Path to where pkg files are downloaded (cache_dir/pkg)
# * cache_ttl    - Max age (in seconds) of TSV files before they are refreshed
#
---
"""
