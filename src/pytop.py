#!/usr/bin/env python3

""" pytop.py: Htop copycat implemented in Python. """
import datetime

__author__ = 'Andrii Oshtuk'
__copyright__ = '(C) 2019 ' + __author__
__license__ = "MIT"
__version__ = '0.0.1 Alpha 1'

import argparse
from collections import namedtuple
import time


class Utilities:


    @staticmethod
    def to_bytes(value, unit):
        if unit == 'gB':
            return value * 1024 * 1024
        elif unit == 'kB':
            return value * 1024
        return value



class Cpu:
    """
    Calculates CPU usage based on /proc/stat file data

    Class retrieves CPU statistics from /proc/stat file and provides public
    methods for easy access to CPU usage.

    Attributes:
        update(): Retrieves fresh CPU statistics.
        cpu_usage(): List of CPUs usage for each CPU measured between last two update() calls.

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


class MemInfo:
    """
    Information about memory usage, both physical and swap.

    Class retrieves statistics about memory usage on the system and provides public
    properties for easy access to the amount of free and used memory (both physical and swap)
    on the system as well as the shared memory and buffers used by the kernel.

    Attributes:
        update(): Retrieves fresh memory statistics from /proc/meminfo.
        total_memory(): Returns total usable RAM (i.e., physical RAM minus a few reserved bits and the kernel binary code).
        used_memory(): TODO(AOS)
        buffers(): Returns relatively temporary storage for raw disk blocks
        cache(): Returns in-memory cache for files read from the disk (the page cache)
        total_swap(): Returns total amount of swap space available.
        free_swap(): Returns amount of swap space that is currently unused.

    .. PROC(5)
        http://man7.org/linux/man-pages/man5/proc.5.html
    """
    def __init__(self):
        self.__total_memory = None
        self.__used_memory = None
        self.__buffers = None
        self.__cache = None
        self.__total_swap = None
        self.__free_swap = None
        self.__mem_info = {}

        self.update()

    @property
    def total_memory(self):
        """Returns total usable RAM (i.e., physical RAM minus a few reserved bits and the kernel binary code)."""
        return self.__total_memory

    @property
    def used_memory(self):
        """TODO(AOS)"""
        return self.__used_memory

    @property
    def buffers(self):
        """Returns relatively temporary storage for raw disk blocks"""
        return self.__buffers

    @property
    def cache(self):
        """Returns in-memory cache for files read from the disk (the page cache)"""
        return self.__cache

    @property
    def total_swap(self):
        """Returns total amount of swap space available."""
        return self.__total_swap

    @property
    def free_swap(self):
        """Returns amount of swap space that is currently unused."""
        return self.__free_swap

    def update(self):
        """Retrieves fresh memory statistics from /proc/meminfo."""
        self._read_file()
        self.__total_memory = self.__mem_info.get('MemTotal:', 0.0)
        self.__used_memory = self.__total_memory - self.__mem_info.get('MemFree:', 0.0)
        self.__buffers = self.__mem_info.get('Buffers:', 0.0)

        cached = self.__mem_info.get('Cached:', 0.0)
        s_reclaimable = self.__mem_info.get('SReclaimable:', 0.0)
        shmem = self.__mem_info.get('Shmem:', 0.0)
        self.__cache = cached + s_reclaimable + shmem

        self.__total_swap = self.__mem_info.get('SwapTotal:', 0.0)
        self.__free_swap = self.__mem_info.get('SwapFree:', 0.0)

    def _read_file(self):
        with open('/proc/meminfo', 'r') as file:
            for line in file:
                field, value, *unit = line.split()
                if not unit:
                    unit.append('B')
                self.__mem_info[field] = Utilities.to_bytes(int(value), unit)


def parse_args():
    """ Returns script options parsed from CLI arguments."""
    argparser = argparse.ArgumentParser(prog='pytop')
    argparser.add_argument('-v', '--version', action='version',
                           version='%(prog)s ' + __version__ + ' - ' + __copyright__)

    return argparser.parse_args()

if __name__ == "__main__":
    options = parse_args()

    # test logic
    cpu = Cpu()
    time.sleep(1)
    cpu.update()
    for i, pct in enumerate(cpu.cpu_usage):
        print(f"{i} = {pct} %")

    memory = MemInfo()
    print(f"total = {memory.total_memory/(1024*1024)} gB")
    m = memory.used_memory - memory.cache - memory.buffers
    print(f"used = {m / (1024 * 1024)} gB")

    print(f"\nswap:{(memory.total_swap - memory.free_swap)/ (1024 )}/{memory.total_swap/ (1024 * 1024)}gB")
