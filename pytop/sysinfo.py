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
    """
        Information about running process with PID.

        Class retrieves all statistics (state, niceness, priority, user, time, memory and cpu usage)
        for a running process and provides public properties for easy access.

        Example:
            >>> Process.set_uptime(obj) # requires object with uptime attribute holding actual uptime
            >>> Process.set_memory_info(value) # requires to set memory size
            >>> proc = Process(4)
            >>> proc.pid, proc.priority, proc.niceness
            (1, 20, 0)

        Attributes:
            update(): Retrieves actual process statistics from /proc/[pid]/ subdirectory.
            pid: process PID
            user: process user
            priority: process kernel-space priority
            niceness: process user-space niceness
            virtual_memory: virtual memory requested by process
            resident_memory: resident memory usage (currently being used)
            shared_memory: shared memory used
            state: process state
            cpu_usage: percentage of CPU time process is currently using
            memory_usage: task's current share of the phisical memory
            time(): returns processor time used by process
            command: command that launched process

        .. PROC(5)
            http://man7.org/linux/man-pages/man5/proc.5.html
        """

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

        self.kthread = False # TODO(AOS) What for?
        self.update()

    def update(self):
        """Retrieves actual process statistics from /proc/[pid]/ subdirectory."""
        try:
            self._read_cmdline()
            self._read_stat()
            self._read_status()
        except (ValueError, IndexError):
            raise SystemInfoError('Error while parsing /proc/[pid]/ subdirectory')

    def _read_cmdline(self):
        filename = f'{Process._proc_folder}/{self.pid}/cmdline'
        with open(filename, 'r') as file:
            self.command = Process._remove_whitespaces(file.read())

    def _read_stat(self):
        filename = f'{Process._proc_folder}/{self.pid}/stat'
        with open(filename, 'r') as file:
            values = ['Reserved']
            values += file.read().split()

            if not self.command:
                self.command = Process._remove_whitespaces(values[2][1:-1])

            self.kthread = True if int(values[9]) & 0x00200000 else False
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

    def _read_status(self):
        filename = f'{Process._proc_folder}/{self.pid}/status'
        status = {}

        with open(filename, 'r') as file:
            for line in file:
                temp = line.split()
                name = temp[0][:-1]
                if name in ('Name', 'State'):
                     status[name] = temp[1]
                if name in ('Uid', 'VmSize', 'VmRSS', 'RssShmem'):
                    status[name] = int(temp[1])

            # mandatory properties raise exception
            if not self.command:
                self.command = status['Name']
            self.state = status['State']
            user_id = status['Uid']
            # self.user = pwd.getpwuid( int(user_id)).pw_name  # TODO(AOS) Pycharm creates local environment where there are no other user

            # optional properties
            self.virtual_memory = status.get('VmSize', 0)
            self.resident_memory = status.get('VmRSS', 0)
            self.shared_memory = status.get('RssShmem', 0)

        memory_usage = self.resident_memory * 100 / Process._total_memory
        self.memory_usage = round(memory_usage, 1)

    @property
    def time(self):
        """:obj:'str': Returns processor time used by process."""
        d = timedelta(seconds=float(self._time))

        hours, remainder = divmod(d.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0.0:
            return '%dh%d:%d' % (int(hours), int(minutes), int(seconds))
        else:
            return '%.0f:%05.2f' % (minutes, seconds)

    @staticmethod
    def set_uptime(obj):
        """Process class requires object with uptime attribute holding actual uptime"""
        Process._uptime = obj

    @staticmethod
    def set_memory_info(total_memory):
        """Process class requires to know total RAM size (int value)"""
        Process._total_memory = total_memory

    @staticmethod
    def _remove_whitespaces(string):
        return string.replace('\x00', ' ').rstrip()


class ProcessesController:
    # TODO(AOS) Add docstrings
    _proc_folder = '/proc/'

    def __init__(self, uptime, memory):
        self._processes = set()
        self._previous_procceses = set()
        Process.set_uptime(uptime)
        Process.set_memory_info(memory)
        self.update()

    def update(self):
        actual_processes = {
            pid for pid in os.listdir(ProcessesController._proc_folder)
            if os.path.isdir(ProcessesController._proc_folder + pid) and pid.isdigit()
        }

        obsolete = self._previous_procceses - actual_processes
        new = actual_processes - self._previous_procceses

        for process in self._processes:
            if process.pid in obsolete:
                del process
        for pid in new:
            self._processes.add(Process(pid))
        self._previous_procceses = actual_processes

    @property
    def processes(self):
        return self._processes

    @property
    def proccesses_number(self):
        return len(self._processes)

    @property
    def running_proccesses_number(self):
        # TODO(eric): Is this supposed to be non-zombie procs? Or num threads?
        return self.proccesses_number

    @property
    def processes_pid(self):
        return [int(process.pid) for process in self._processes]


class Utility:
    """
        Class provides utility methods.

        Attributes:
            kb_to_xb(): Converts memory size in kB into string representation.
    """

    @staticmethod
    def kb_to_xb(kb):
        """Converts memory size in kB into string representation."""
        if not isinstance(kb, int):
            raise TypeError

        if kb < 100 * 1024:
            return f'{kb}'
        elif kb < 1024 * 1024:
            return f'{kb // 1024}M'
        else:
            return f'{kb // (1024 * 1024)}G'
