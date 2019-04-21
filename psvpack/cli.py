#!/usr/bin/env python3
# vim: set ts=4 sw=4 expandtab syntax=python:
"""

psvpack.cli
PS Vita package tool
CLI entry-point

@author   Jacob Hipps <jacob@ycnrg.org>

Copyright (c) 2018 J. Hipps / Neo-Retro Group, Inc.
https://ycnrg.org/

"""

import os
import sys
import logging
from argparse import ArgumentParser

from psvpack import __version__, __date__
from psvpack import psfree
from psvpack.util import *

logger = logging.getLogger('psvpack')


def setup_logging(clevel=logging.INFO, flevel=logging.DEBUG, logfile=None):
    """configure logging using standard logging module"""
    logger.setLevel(logging.DEBUG)

    con = logging.StreamHandler()
    con.setLevel(clevel)
    con_format = logging.Formatter("%(levelname)s: %(message)s")
    con.setFormatter(con_format)
    logger.addHandler(con)

    if logfile:
        try:
            flog = logging.handlers.WatchedFileHandler(logfile)
            flog.setLevel(flevel)
            flog_format = logging.Formatter("[%(asctime)s] %(name)s: %(levelname)s: %(message)s")
            flog.setFormatter(flog_format)
            logger.addHandler(flog)
        except Exception as e:
            logger.warning("Failed to open logfile %s: %s", logfile, str(e))

def parse_cli(show_help=False):
    """parse CLI options with argparse"""
    aparser = ArgumentParser(description="PSVita pkg helper", usage="psvpack [-d] [-V|-h] [-c PATH] [-r PATH] [-g <PSV|PSV_DLC|...>]\n               [-N] [-X] [-a|-e|-U|-J|-A] [--getall] COMMAND GAME_OR_ID")

    # use defaults stored in __init__
    aparser.set_defaults(loglevel=logging.INFO, command=None, uxroot='./', install=True, noverify=False,
                         glist="PSV", regions=['US', 'JP'], config=get_platform_confpath('config.yaml'))

    aparser.add_argument("command", action="store", nargs="?", metavar="COMMAND", help="Command [search, install]")
    aparser.add_argument("game", action="store", nargs="?", metavar="GAME", help="Search term, Title ID, or package filename")
    aparser.add_argument("--uxroot", "-r", action="store", metavar="PATH", help="path to ux0 root (connected Vita or mounted SD card)")
    aparser.add_argument("--glist", "-g", action="store", metavar="LIST", help="game list [PSV*,PSM,PSX,PSP,PSV_DLC,PSP_DLC]")
    aparser.add_argument("--config", "-c", action="store", metavar="PATH", help="config file [default: %%default]")
    aparser.add_argument("--noinstall", "-N", dest="install", action="store_false", help="download pkg only; do NOT install")
    aparser.add_argument("--noverify", "-X", action="store_true", help="skip existing PKG checksum verification")
    aparser.add_argument("--getall", action="store_true", help="fetch all related items (eg. for DLC)")
    aparser.add_argument("--allregions", "-a", action="store_const", const=['US', 'JP', 'EU', 'ASIA'], help="show all regions (default: only show US and JP)")
    aparser.add_argument("--english", "-e", action="store_const", const=['US', 'EU'], help="show English games only (US and EU)")
    aparser.add_argument("--us", "-U", action="store_const", const=['US'], help="show US region only")
    aparser.add_argument("--eu", "-E", action="store_const", const=['EU'], help="show EU region only")
    aparser.add_argument("--jp", "-J", action="store_const", const=['JP'], help="show JP region only")
    aparser.add_argument("--asia", "-A", action="store_const", const=['ASIA'], help="show ASIA region only")

    aparser.add_argument("--debug", "-d", dest="loglevel", action="store_const", const=logging.DEBUG,
                         help="Enable debug logging")
    aparser.add_argument("--version", "-V", action="version", version="%s (%s)" % (__version__, __date__))

    if show_help:
        aparser.print_help()
        sys.exit(1)

    return aparser.parse_args()

def _main():
    """
    Entry point
    """
    opts = parse_cli()
    setup_logging(clevel=opts.loglevel)
    uconfig = load_config(opts.config)

    if opts.command is None:
        parse_cli(show_help=True)

    if opts.command[0] == 's':
        psfree.do_search(opts.game, uconfig, glist=opts.glist, regions=opts.regions)
    elif opts.command[0] == 'i':
        psfree.get_game(opts.game, uconfig, glist=opts.glist, uxroot=opts.uxroot, install=opts.install, noverify=opts.noverify, getall=opts.getall)

if __name__ == '__main__':
    _main()
