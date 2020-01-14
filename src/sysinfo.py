#!/usr/bin/env python3

""" sysinfo.py: Collection of classes to read Linux system information. """

__author__ = 'Andrii Oshtuk'
__copyright__ = '(C) 2019 ' + __author__
__license__ = "MIT"
__version__ = '1.0.0'

from collections import namedtuple
from datetime import timedelta


class SystemInfoError(Exception):
    """Raised when error occur during system information access"""
    pass


class Cpu:
    """
    Calculates CPU usage based on /proc/stat file data

    Class retrieves CPU statistics from /proc/stat file and provides public
    methods for easy access to CPU usage.

    Attributes:
        update(): Retrieves fresh CPU statistics.
        cpu_usage: List of CPUs usage per CPU measured between last two update() calls.

    .. PROC(5)
        http://man7.org/linux/man-pages/man5/proc.5.html
    """

    CpuStat = namedtuple('CpuStat', ['name', 'user', 'nice', 'system', 'idle', 'iowait',
                                     'irq', 'softirq', 'steal', 'guest', 'guest_nice'])

    def __init__(self):
        self.prev_stat = Cpu._read_file()
        self.curr_stat = self.prev_stat

    def update(self):
        """ Retrieves fresh CPU statistics and stores previous statistics. """
        self.prev_stat = self.curr_stat
        self.curr_stat = Cpu._read_file()

    @property
    def cpu_usage(self) -> list:
        """:obj:`list` of :obj:`float`: List of CPU usage per CPU measured between last two update() calls."""
        cpu_usage = []

        for prev, new in zip(self.prev_stat, self.curr_stat):
            idle_prev = prev.idle + prev.iowait
            non_idle_prev = prev.user + prev.nice + prev.system + prev.irq + prev.softirq + prev.steal
            total_prev = idle_prev + non_idle_prev

            idle_new = new.idle + new.iowait
            non_idle_new = new.user + new.nice + new.system + new.irq + new.softirq + new.steal
            total_new = idle_new + non_idle_new

            total_diff = total_new - total_prev
            idle_diff = idle_new - idle_prev

            if total_diff <= 0:
                cpu_usage.append(0.0)
                continue

            cpu_usage_pct = (total_diff - idle_diff) * 100 / total_diff
            cpu_usage.append(cpu_usage_pct)

        return cpu_usage

    @staticmethod
    def _read_file() -> list:
        lst = []
        with open('/proc/stat') as file:
            for line in file:
                if line.startswith('cpu '):
                    continue
                elif line.startswith('cpu'):
                    name, *values = line.split()
                    values = map(int, values)
                    temp_tuple = Cpu.CpuStat(name, *values)
                    lst.append(temp_tuple)
        if not lst:
            raise SystemInfoError('Cannot parse /proc/stat file')

        return lst


class LoadAverage:
    """
        The load average over 1, 5, and 15 minutes.

        Class holds load average figures giving the number of jobs in the run queue (state R) or waiting for disk I/O
        (state D) averaged over 1, 5, and 15 minutes.

        Attributes:
            update(): Retrieves actual load average value from /proc/loadavg.
            load_average: Returns load average over 1, 5, and 15 minutes.
            load_average_as_string: Returns load average as a formatted string 'x.xx x.xx x.xx'.

        .. PROC(5)
            http://man7.org/linux/man-pages/man5/proc.5.html
    """

    def __init__(self):
        self._load_average = LoadAverage._read_file()

    def update(self):
        """Retrieves actual load average value from /proc/loadavg."""
        self._load_average = LoadAverage._read_file()

    @staticmethod
    def _read_file():
        with open('/proc/loadavg') as file:
            try:
                t1, t5, t15, *_ = file.read().split()
                values = map(float, [t1, t5, t15])
                return tuple(values)
            except (ValueError, TypeError):
                raise SystemInfoError('Cannot parse /proc/loadavg file')

    @property
    def load_average(self):
        """:obj:`tuple` of :obj:`float`: Returns load average over 1, 5, and 15 minutes."""
        return self._load_average

    @property
    def load_average_as_string(self):
        """:obj:`str`: Returns load average as a formatted string 'x.xx x.xx x.xx'."""
        return f"{self._load_average[0]} {self._load_average[1]} {self._load_average[2]}"


class Uptime:
    """
        The uptime of the system

        Class holds system uptime (including time spent in suspend) fetched from /proc/uptime file.

        Attributes:
            update(): Retrieves actual uptime value from /proc/uptime.
            uptime: Returns system uptime (including time spent in suspend) in seconds.
            uptime_as_string: Returns uptime as a formatted string 'dd hh:mm:ss'

        .. PROC(5)
            http://man7.org/linux/man-pages/man5/proc.5.html
    """

    def __init__(self):
        self._uptime = Uptime._read_file()

    def update(self):
        """Retrieves actual uptime value from /proc/uptime."""
        self._uptime = Uptime._read_file()

    @staticmethod
    def _read_file():
        with open('/proc/uptime') as file:
            try:
                value = file.read().split()[0]
                return int(float(value))
            except (IndexError, ValueError, TypeError):
                raise SystemInfoError('Cannot parse /proc/uptime file')

    @property
    def uptime(self):
        """:obj:`int`: Returns system uptime (including time spent in suspend) in seconds."""
        return self._uptime

    @property
    def uptime_as_string(self):
        """:obj:`str`: Returns uptime as a formatted string 'dd hh:mm:ss'"""
        uptime = timedelta(seconds=self._uptime)
        return f"{uptime}"
