#!/usr/bin/env python3

""" sysinfo.py: Collection of classes to read Linux system information. """

__author__ = 'Andrii Oshtuk'
__copyright__ = '(C) 2019 ' + __author__
__license__ = "MIT"
__version__ = '0.0.1 Alpha 1'

import os
import os
import pwd
from collections import namedtuple
from datetime import timedelta


class Cpu:
    """
    Calculates CPU usage based on /proc/stat file data

    Class retrieves CPU statistics from /proc/stat file and provides public
    methods for easy access to CPU usage.

    Attributes:
        update(): Retrieves fresh CPU statistics.
        cpu_usage: List of CPUs usage for each CPU measured between last two update() calls.

    .. PROC(5)
        http://man7.org/linux/man-pages/man5/proc.5.html
    """

    CpuStat = namedtuple('CpuStat',
                         ['name', 'user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest',
                          'guest_nice'])

    def __init__(self):
        self.prev_stat = self._read_file()
        self.current_stat = self.prev_stat

    def update(self):
        """ Retrieves fresh CPU statistics and stores previous statistics. """
        self.prev_stat = self.current_stat
        self.current_stat = self._read_file()

    @property
    def cpu_usage(self):
        """ List of CPU usage for each CPU measured between last two update() calls."""
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

            if not total_diff:
                cpu_usage.append(0.0)
                continue

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
                    values = map(int, line.split()[1:])
                    temp = Cpu.CpuStat(line.split()[0], *values)
                    lst.append(temp)

        return lst