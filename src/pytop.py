#!/usr/bin/env python3

""" pytop.py: Htop copycat implemented in Python. """

__author__ = 'Andrii Oshtuk'
__copyright__ = '(C) 2019 ' + __author__
__license__ = "MIT"
__version__ = '0.0.1 Alpha 1'

import datetime
import urwid
import argparse
from collections import namedtuple
from  datetime import timedelta
import time
import os
import pwd
import sys


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

    @property
    def total_used_memory(self):
        """TODO(AOS)"""
        return self.__used_memory - self.__buffers - self.__cache

    @property
    def total_used_swap(self):
        """TODO(AOS)"""
        return self.__total_swap - self.__free_swap

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


class Uptime:
    """
        The uptime of the system

        Class holds system uptime (including time spent in suspend) fetched from /proc/uptime file.

        Attributes:
            update(): Retrieves actual uptime value from /proc/uptime.
            uptime: Returns system uptime (including time spent in suspend) in seconds.
            uptime_as_string: Returns uptime as a formatted string

        .. PROC(5)
            http://man7.org/linux/man-pages/man5/proc.5.html
        """
    def __init__(self):
        self.__uptime = None
        self.update()

    def update(self):
        """Retrieves actual uptime value from /proc/uptime."""
        self._read_file()

    def _read_file(self):
        with open('/proc/uptime', 'r') as file:
            value = file.read().split()[0]
            self.__uptime = int(float(value))

    @property
    def uptime(self):
        """Returns system uptime (including time spent in suspend) in seconds."""
        return self.__uptime

    @property
    def uptime_as_string(self):
        """Returns uptime as a formatted string"""
        uptime = timedelta(seconds=self.__uptime)
        return f"{uptime}"


class LoadAverage:
    """
        The load average over 1, 5, and 15 minutes.

        Class holds load average figures giving the number of jobs in the run queue (state R) or waiting for disk I/O
        (state D) averaged over 1, 5, and 15 minutes.

        Attributes:
            update(): Retrieves actual load average value from /proc/loadavg.
            load_average: Returns load average over 1, 5, and 15 minutes.
            load_average_as_string: Returns load average as a formatted string

        .. PROC(5)
            http://man7.org/linux/man-pages/man5/proc.5.html
        """
    def __init__(self):
        self.__load_average = (None, None, None)
        self.update()

    def update(self):
        """Retrieves actual load average value from /proc/loadavg."""
        self._read_file()

    def _read_file(self):
        with open('/proc/loadavg', 'r') as file:
            values = file.read().split()[:3]
            values = map(float, values)
            self.__load_average = tuple(values)

    @property
    def load_average(self):
        """Returns load average over 1, 5, and 15 minutes."""
        return self.__load_average

    @property
    def load_average_as_string(self):
        """Returns load average as a formatted string"""
        return f"{self.__load_average[0]} {self.__load_average[1]} {self.__load_average[2]}"


class Process:
    uptime = None
    memory_info = None

    def __init__(self, pid):
        self.__pid = pid
        self.__user = None
        self.__priority = None
        self.__niceness = None
        self.__virtual_memory = None
        self.__resident_memory = None
        self.__shared_memory = None
        self.__state = None
        self.__cpu_usage = None
        self.__memory_usage = None
        self.__time = None
        self.__command = None
        self.__clock_ticks_per_second = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

        self.__is_kthread = False
        self.update()

    def update(self):
        self.read_cmdline()
        self.read_stat()
        self.read_status()

    def read_cmdline(self):
        """ Returns the command that originally started the process (content of /proc/PID/cmdline) """
        filename = f'/proc/{self.__pid}/cmdline'
        with open(filename, 'r') as file:
            self.__command = file.read()

    def read_stat(self):
        PF_KTHREAD = 0x00200000  # TODO(AOS) Redo

        filename = f'/proc/{self.__pid}/stat'
        with open(filename, 'r') as file:
            text = 'None '
            text = text + file.read()
            self.__is_kthread = True if int(text.split()[9]) & PF_KTHREAD else False
            self.__priority = text.split()[18]  # TODO(AOS) Why the heck are you calling split so many times?
            self.__niceness = text.split()[19]
            total_time_ticks = int(text.split()[14]) + int(text.split()[15]) + int(text.split()[16]) + int(text.split()[17])
            start_time_ticks = int(text.split()[22])
            process_time_ticks = int(text.split()[14]) + int(text.split()[15])

            seconds = Process.uptime.uptime - start_time_ticks / self.__clock_ticks_per_second
            self.__cpu_usage = 100 * ((total_time_ticks / self.__clock_ticks_per_second) / seconds)

            self.__time = format(process_time_ticks/ self.__clock_ticks_per_second, '.2f')  # TODO(AOS) Add proper format as HH:SS.XX

    def read_status(self):  # TODO(AOS) Add user_name
        """ Returns the tuple (process_state, process_virtmemory)  (content of /proc/PID/status) """  # TODO(AOS) Add user_name
        filename = f'/proc/{self.__pid}/status'

        with open(filename, 'r') as file:
            for line in file:
                if 'State:' in line:
                    self.__state = line.split()[1]
                elif 'Uid:' in line:
                    user_id = line.split()[1]  # TODO(AOS) figure out whatever to use real or effective UID
                    self.__user = pwd.getpwuid(int(user_id)).pw_name
                elif 'VmSize:' in line:
                    # process_vmsize = int(line.split()[1])/1024 #TODO(AOS) handles mB, kB properly
                    vmsize = int(line.split()[1])
                    self.__virtual_memory = str(vmsize // 1024) + 'M' if vmsize > 1024 else str(vmsize)
                    # process_vmsize = format(int(process_vmsize), 'd')
                elif 'VmRSS:' in line:
                    self.__resident_memory = line.split()[1]  # TODO(AOS) Redo
                    # print(process_vm_rss_size)
                elif 'RssShmem:' in line:
                    self.__shared_memory = line.split()[1]  # TODO(AOS) Redo

        # TODO(AOS) Uncomment!!!!
        # if self.__resident_memory != ' ':
        #     self.__memory_usage = int(self.__resident_memory) * 100 / int(Process.memory_info.total_memory)
        # else:
        #     self.__memory_usage = ' '

    @staticmethod
    def set_uptime(obj):
        Process.uptime = obj

    @staticmethod
    def set_memory_info(obj):
        Process.memory_info = obj

    @property
    def pid(self):
        return self.__pid

    @property
    def user(self):
        return self.__user

    @user.setter
    def user(self, value):
        self.__user = value

    @property
    def priority(self):
        return self.__priority

    @property
    def niceness(self):
        return self.__niceness

    @niceness.setter
    def niceness(self, value):
        self.__niceness = value

    @property
    def virtual_memory(self):
        return self.__virtual_memory

    @virtual_memory.setter
    def virtual_memory(self, value):
        self.__virtual_memory = value

    @property
    def resident_memory(self):
        return self.__resident_memory

    @resident_memory.setter
    def resident_memory(self, value):
        self.__resident_memory = value

    @property
    def shared_memory(self):
        return self.__shared_memory

    @shared_memory.setter
    def shared_memory(self, value):
        self.__shared_memory = value

    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, value):
        self.__state = value

    @property
    def cpu_usage(self):
        return self.__cpu_usage

    @cpu_usage.setter
    def cpu_usage(self, value):
        self.__cpu_usage = value

    @property
    def memory_usage(self):
        return self.__memory_usage

    @memory_usage.setter
    def memory_usage(self, value):
        self.__memory_usage = value

    @property
    def time(self):
        return self.__time

    @time.setter
    def time(self, value):
        self.__time = value

    @property
    def command(self):
        return self.__command

    @command.setter
    def command(self, value):
        self.__command

    @property
    def is_running(self):
        return self.__state == 'R'

    @property
    def is_sleeping(self):
        return self.__state == 'S'

    @property
    def is_zombie(self):
        return self.__state == 'Z'

    @property
    def is_stopped(self):
        return self.__state in 'Tt'

    def __str__(self):
        return f'{self.__pid} {self.__user} {self.__priority} {self.__niceness} {self.__virtual_memory} ' \
               f'{self.__resident_memory} {self.__shared_memory} {self.__state} {self.__cpu_usage} ' \
               f'{self.__memory_usage} {self.__time} {self.__command}'

def parse_args():
    """ Returns script options parsed from CLI arguments."""
    argparser = argparse.ArgumentParser(prog='pytop')
    argparser.add_argument('-v', '--version', action='version',
                           version='%(prog)s ' + __version__ + ' - ' + __copyright__)

    return argparser.parse_args()


def from_kB(value):
    result = (0.0, ' ')
    if value < 1024:
        prefix = (value, 'K')
    elif value < 1024*1024:
        prefix = (value/1024, 'M')
    elif value < 1024*1024*1024:
        prefix = (value/(1024*1024), 'G')
    return prefix

class CpuAndMemoryPanel(urwid.WidgetWrap):
    """docstring for CpuAndMemoryPanel"""
    def __init__(self, cpu, memory):

        self.__cpu = cpu
        self.__memory = memory
        self.__widgets = []

        for i, value in enumerate(self.__cpu.cpu_usage):
            self.__widgets.append(urwid.Text(self._cpu_progress_markup(i+1, 0.0)))

        self.__widgets.append(urwid.Text(self._mem_usage_markup('Mem',0.0, 0.0)))
        self.__widgets.append(urwid.Text(self._mem_usage_markup('Swp',0.0, 0.0)))
        self.__panel = urwid.Pile(self.__widgets)
        urwid.WidgetWrap.__init__(self, self.__panel)

    def refresh(self):
        for i, value in enumerate(self.__cpu.cpu_usage):
            self.__widgets[i].set_text(self._cpu_progress_markup(i+1, value))

        self.__widgets[-1].set_text(self._mem_usage_markup('Mem', self.__memory.total_used_memory, self.__memory.total_memory))
        self.__widgets[-2].set_text(self._mem_usage_markup('Swp', self.__memory.total_used_swap, self.__memory.total_swap))

    def _cpu_progress_markup(self, index, percent, width=29):
        pct = "%4.1f" % percent
        bars = int(percent*width/100)
        fill = width - bars
        return [
        ('fields_names', u'%-3.2s' % index),
        ('progress_bracket', u'['),
        ('progress_bar', u'|'*bars),
        ('progress_bar', u' ' * fill),
        ('cpu_pct', u'%5.5s%%' % pct),
        ('progress_bracket', u']')
        ]

    def _mem_usage_markup(self, txt, used, total, width=24):
        used_mem = from_kB(used)
        total_mem = from_kB(total)

        if total > 0:
            bars = int(used * width / total)
        else:
            bars = 0

        fill = width - bars

        return [
        ('fields_names', txt),
        ('progress_bracket', u'['),
        ('progress_bar', u'|'*bars),
        ('progress_bar', u' ' * fill),
        ('cpu_pct', u'%4.4s%c/%4.4s%c' % (used_mem[0], used_mem[1], total_mem[0], total_mem[1])),
        ('progress_bracket', u']')
        ]


class Application(object):

    def __init__(self):
        self._cpu = Cpu()
        self._memory = MemInfo()
        self._data = [self._cpu, self._memory]

        self._cpu_and_memory_panel = CpuAndMemoryPanel(self._cpu, self._memory)

        self._fill = urwid.Filler(self._cpu_and_memory_panel, 'top')
        self._loop = urwid.MainLoop(self._fill,
        	unhandled_input = self._handle_input
        )

        self._loop.set_alarm_in(1, self.refresh)

    def refresh(self, loop, data):
        # Update data here
        for i in self._data:
            i.update()

        self._loop.set_alarm_in(1, self.refresh)
        self._cpu_and_memory_panel.refresh()

    def start(self):
        self._loop.run()

    def display_help(self):

        help_screen = urwid.Overlay(
            self._help_txt,
            self._fill,
            align = 'center',
            width = 40,
            valign = 'middle',
            height = 10)

        self._loop.widget = help_screen

    def _handle_input(self, key):

        if type(key) == str:
            if key in ('q', 'Q'):
                raise urwid.ExitMainLoop()
            elif key in ('h', 'H'):
                self.display_help()
        elif type(key) == tuple:
            pass

    def cpu_progress_markup(self, index, percent, width=29):
        pct = "%4.1f" % percent
        bars = int(percent * width / 100)
        fill = width - bars
        return [
            ('fields_names', u'%-3.2s' % index),
            ('progress_bracket', u'['),
            ('progress_bar', u'|' * bars),
            ('progress_bar', u' ' * fill),
            ('cpu_pct', u'%5.5s%%' % pct),
            ('progress_bracket', u']')
        ]

    def mem_usage_markup(self, txt, used, total, width=24):
        used_mem = self.from_kB(used)
        total_mem = self.from_kB(total)

        if total > 0:
            bars = int(used * width / total)
        else:
            bars = 0

        fill = width - bars

        return [
            ('fields_names', txt),
            ('progress_bracket', u'['),
            ('progress_bar', u'|' * bars),
            ('progress_bar', u' ' * fill),
            ('cpu_pct', u'%4.4s%c/%4.4s%c' % (used_mem[0], used_mem[1], total_mem[0], total_mem[1])),
            ('progress_bracket', u']')
        ]

    def from_kB(self, value):
        result = (0.0, ' ')
        if value < 1024:
            prefix = (value, 'K')
        elif value < 1024 * 1024:
            prefix = (value / 1024, 'M')
        elif value < 1024 * 1024 * 1024:
            prefix = (value / (1024 * 1024), 'G')
        return prefix

if __name__ == "__main__":
    options = parse_args()

    Application().start()

    sys.exit(0)

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

    up = Uptime()
    print(f"Uptime:{up.uptime_as_string}")

    load = LoadAverage()
    print(f"Load average:{load.load_average}")

    Process.set_uptime(up)
    Process.set_memory_info(memory)
    processes = [Process(name) for name in os.listdir("/proc") if os.path.isdir("/proc/" + name) and name.isdigit()]
    for p in processes[:]:
        p.update()
        print(p)

