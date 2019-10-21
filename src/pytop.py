#!/usr/bin/env python3

""" pytop.py: Htop copycat implemented in Python. """
import datetime

__author__ = 'Andrii Oshtuk'
__copyright__ = '(C) 2019 ' + __author__
__license__ = "MIT"
__version__ = '0.0.1 Alpha 1'

import argparse

def parse_args():
    """ Returns script options parsed from CLI arguments."""
    argparser = argparse.ArgumentParser(prog='pytop')
    argparser.add_argument('-v', '--version', action='version',
                           version='%(prog)s ' + __version__ + ' - ' + __copyright__)

    return argparser.parse_args()

if __name__ == "__main__":
    options = parse_args()