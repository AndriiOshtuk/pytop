#!/usr/bin/env python3

""" sysinfo.py: Collection of classes to read Linux system information. """

__author__ = 'Andrii Oshtuk'
__copyright__ = '(C) 2019 ' + __author__
__license__ = "MIT"
__version__ = '1.0.0'

from collections import namedtuple
from datetime import timedelta
import os
import pwd


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

    # TODO(AOS): change load_average to field from property
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


class MemInfo:
    """
    Information about memory usage, both physical and swap.

    Class retrieves statistics about memory usage on the system and provides public
    properties for easy access to the amount of free and used memory (both physical and swap).

    Attributes:
        update(): Retrieves actual memory statistics from /proc/meminfo.
        total_memory(): Returns total amount of RAM space available.
        used_memory(): Returns amount of RAM space that is currently used.
        total_swap(): Returns total amount of swap space available.
        used_swap(): Returns amount of swap space that is currently used.

    .. PROC(5)
        http://man7.org/linux/man-pages/man5/proc.5.html
    """
    def __init__(self):
        self._total_memory = None
        self._used_memory = None
        self._total_swap = None
        self._used_swap = None
        self.update()

    def update(self):
        """Retrieves actual memory information from /proc/meminfo.

        .. Stackoverflow htop author explanation
            https://stackoverflow.com/a/41251290
        """
        info = MemInfo._read_file()

        try:
            self._total_memory = info['MemTotal']
            # See link for calculation explanation
            used_memory = info['MemTotal'] - info['MemFree'] - info['Buffers'] - info['Cached'] - \
                          info['SReclaimable'] + info['Shmem']
            self._used_memory = used_memory
            self._total_swap = info['SwapTotal']
            self._used_swap = info['SwapTotal'] - info['SwapFree']
        except KeyError:
            raise SystemInfoError('Cannot parse /proc/meminfo file')

    @property
    def total_memory(self):
        """:obj:'int': Returns total amount of RAM space available."""
        return self._total_memory

    @property
    def used_memory(self):
        """:obj:'int': Returns amount of RAM space that is currently used."""
        return self._used_memory

    @property
    def total_swap(self):
        """:obj:'int': Returns total amount of swap space available."""
        return self._total_swap

    @property
    def used_swap(self):
        """:obj:'int': Returns amount of swap space that is currently used."""
        return self._used_swap

    @staticmethod
    def _read_file():
        meaningful_fields = ['MemTotal', 'MemFree', 'Buffers', 'Cached', 'SReclaimable',
                             'Shmem', 'SwapTotal', 'SwapFree']
        values = {}
        with open('/proc/meminfo') as file:
            for line in file:
                try:
                    field, value, *unit = line.split()
                    name = field[:-1]
                    if name in meaningful_fields:
                        values[name] = int(value)
                except (IndexError, ValueError, TypeError):
                    raise SystemInfoError('Cannot parse /proc/meminfo file')

        return values

class Process:

    _proc_folder = '/proc'
    _clock_ticks_per_second = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
    _uptime = None
    _total_memory = None

    def __init__(self, pid):
        self.pid = pid
        self.user = None
        self.priority = None
        self.niceness = None
        self.virtual_memory = 0  # memory must be initialized with 0
        self.resident_memory = 0
        self.shared_memory = 0
        self.state = None
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self._time = 0.0
        self.command = ''

        self._time_ticks_old = None
        self._uptime_old = None

        self._is_kthread = False # TODO(AOS) What for?
        self.update()

    def update(self):
        self._read_cmdline()
        self._read_stat()
        self._read_status()

    def _read_cmdline(self):
        """ Returns the command that originally started the process (content of /proc/PID/cmdline) """
        filename = f'{Process._proc_folder}/{self.pid}/cmdline'
        with open(filename, 'r') as file:
            self.command = Process.remove_whitespaces(file.read())

    def _read_stat(self):
        PF_KTHREAD = 0x00200000  # TODO(AOS) Redo

        filename = f'{Process._proc_folder}/{self.pid}/stat'
        with open(filename, 'r') as file:
            values = ['Reserved']
            values += file.read().split()

            if not self.command:
                self.command = Process.remove_whitespaces(values[2][1:-1])

            self._is_kthread = True if int(values[9]) & PF_KTHREAD else False
            self.priority = values[18]
            self.niceness = values[19]

            time_ticks = sum(map(int, values[14:18]))
            uptime = Process._uptime.uptime

            if self._time_ticks_old is None:
                self._time_ticks_old = time_ticks
            if self._uptime_old is None:
                self._uptime_old = uptime

            seconds = uptime - self._uptime_old
            if seconds <= 0:
                self.cpu_usage = 0.0
            else:
                ticks_diff = time_ticks - self._time_ticks_old
                self.cpu_usage = 100 * ((ticks_diff / self._clock_ticks_per_second) / seconds)
            self._time_ticks_old = time_ticks
            self._uptime_old = uptime

            process_time_ticks = int(values[14]) + int(values[15])
            self._time = process_time_ticks / self._clock_ticks_per_second

    def _read_status(self):  # TODO(AOS) Add user_name
        """ Returns the tuple (process_state, process_virtmemory)  (content of /proc/PID/status) """  # TODO(AOS) Add user_name
        filename = f'{Process._proc_folder}/{self.pid}/status'

        with open(filename, 'r') as file:
            for line in file:
                if not self.command and 'Name' in line:
                    self.command = line.split()[1]
                if 'State:' in line:
                    self.state = line.split()[1]
                elif 'Uid:' in line:
                    user_id = line.split()[1]  # TODO(AOS) figure out whatever to use real or effective UID
                    # self.user = pwd.getpwuid(int(user_id)).pw_name # TODO(AOS) Pycharm creates local environment where there are no other user
                elif 'VmSize:' in line:
                    self.virtual_memory = int(line.split()[1])
                elif 'VmRSS:' in line:
                    self.resident_memory = int(line.split()[1])
                elif 'RssShmem:' in line:
                    self.shared_memory = int(line.split()[1])

        memory_usage = self.resident_memory * 100 / Process._total_memory
        self.memory_usage = round(memory_usage, 1)

    @property
    def time(self):
        d = timedelta(seconds=float(self._time))

        hours, remainder = divmod(d.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0.0:
            return '%dh%d:%d' % (int(hours), int(minutes), int(seconds))
        else:
            return '%.0f:%05.2f' % (minutes, seconds)

    @staticmethod
    def set_uptime(obj):
        Process._uptime = obj

    @staticmethod
    def set_memory_info(total_memory):
        Process._total_memory = total_memory

    @staticmethod
    def remove_whitespaces(string):
        return string.replace('\x00', ' ').rstrip()


class Utility:

    @staticmethod
    def kb_to_xb(kb):
        if not isinstance(kb, int):
            raise TypeError

        if kb < 100 * 1024:
            return f'{kb}'
        elif kb < 1024 * 1024:
            return f'{kb // 1024}M'
        else:
            return f'{kb // (1024 * 1024)}G'
