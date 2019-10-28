#!/usr/bin/env python3

""" pytop.py: Htop copycat implemented in Python. """


__author__ = 'Andrii Oshtuk'
__copyright__ = '(C) 2019 ' + __author__
__license__ = "MIT"
__version__ = '0.0.1 Alpha 1'

import argparse
from collections import namedtuple


Cpu_Statistics = namedtuple('Cpu_Statistics', ['name', 'user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest', 'guest_nice'])

class Cpu:

    def __init__(self):
        self.prev_stat = self._read_file()
        self.current_stat = self.prev_stat

    def update(self):
        self.prev_stat = self.current_stat
        self.current_stat = self._read_file()

    def get_cpu_usage(self):

        cpu_usage = []

        for (prev, new) in zip(self.prev_stat, self.current_stat):
            idle_prev = prev.idle + prev.iowait
            idle_new = new.idle + new.iowait

            non_idle_prev = prev.user + prev.nice + prev.system + prev.irq + prev.softirq + prev.steal
            non_idle_new = new.user + new.nice + new.system + new.irq + new.softirq + new.steal

            total_prev = idle_prev + non_idle_prev
            total_new = idle_new + non_idle_new

            total_diff = total_new - total_prev
            idle_diff = idle_new - idle_prev

            cpu_usage_pct = (total_diff - idle_diff) * 100 / total_diff
            cpu_usage.append(cpu_usage_pct)

        return cpu_usage

    def _read_file(self) -> list:
        lst = []
        with open('/proc/stat') as file:
            for line in file:
                if line.startswith('cpu '):
                    continue
                elif line.startswith('cpu'):
                    temp = namedtuple(*line)
                    lst.append(temp)

        return lst



def parse_args():
    """ Returns script options parsed from CLI arguments."""
    argparser = argparse.ArgumentParser(prog='pytop')
    argparser.add_argument('-v', '--version', action='version',
                           version='%(prog)s ' + __version__ + ' - ' + __copyright__)

    return argparser.parse_args()

if __name__ == "__main__":
    options = parse_args()