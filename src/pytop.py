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

class CPU:
    def __init__(self, name, user = 0, nice = 0, system = 0, idle = 0, iowait = 0, irq = 0, softirq = 0, steal = 0, guest = 0, guest_nice = 0):
        self.name = name
        self.update(user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice)

    def update(self, user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice):
        self.user = user
        self.nice = nice
        self.system = system
        self.idle = idle
        self.iowait = iowait
        self.irq = irq
        self.softirq = softirq
        self.steal = steal
        self.guest = guest
        self.guest_nice = guest_nice

    def __repr__(self):
        return f'CPU: name=\'{self.name}\', ' \
               f'user={self.user}, ' \
               f'nice={self.nice}, ' \
               f'system={self.system}, ' \
               f'idle={self.idle}, ' \
               f'iowait={self.iowait}, ' \
               f'irq={self.irq}, ' \
               f'softirq={self.softirq}, ' \
               f'steal={self.steal}, ' \
               f'guest={ self.guest}, ' \
               f'guest_nice{self.guest_nice}'


class CPU_statistics:
    def __init__(self):
        self.cpu_list = []

        with open('/proc/stat') as f:
            for line in f:
                if line.startswith('cpu '): continue
                if line.startswith('cpu'):
                    cpu = CPU(line.split()[0])
                    self.cpu_list.append(cpu)

        self.update()


    def update(self):
        with open('/proc/stat') as f:
            for i, line in enumerate(f, start = -1):
                if line.startswith('cpu '): continue
                if line.startswith('cpu'):
                    values = line.split()
                    self.cpu_list[i].update(*map(int, values[1:]))

    def __repr__(self):
        s = ''
        for el in self.cpu_list:
            s += el.__repr__()
            s += '\n'

        return s




if __name__ == "__main__":
    options = parse_args()

    a = CPU_statistics()
    print(a)