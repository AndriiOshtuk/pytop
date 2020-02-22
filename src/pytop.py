#!/usr/bin/env python3

""" pytop.py: Htop copycat implemented in Python. """

__author__ = 'Andrii Oshtuk'
__copyright__ = '(C) 2019 ' + __author__
__license__ = "MIT"
__version__ = '1.0.0'

import urwid
import argparse
import sys

from sysinfo import Cpu, MemInfo, Uptime, LoadAverage, ProcessesController, Utility


def parse_args():
    """ Returns script options parsed from CLI arguments."""
    argparser = argparse.ArgumentParser(prog='pytop')
    argparser.add_argument('-v', '--version', action='version',
                           version='%(prog)s ' + __version__ + ' - ' + __copyright__)

    return argparser.parse_args()


class CpuAndMemoryPanel(urwid.WidgetWrap):
    """A pile of widgets (CPU usage, memory and swap usage) stacked vertically from top to bottom

        Args:
            cpu (:obj:'Cpu'): Object that return list of % usage for each CPU.
            memory (:obj:'MemInfo'): Object that return lmemory usage.
    """

    def __init__(self, cpu, memory):
        self.cpu = cpu
        self.memory = memory
        self.widgets = []

        for i, value in enumerate(self.cpu.cpu_usage):
            self.widgets.append(urwid.Text(self.cpu_markup(i + 1, 0.0)))
        self.widgets.append(urwid.Text(self.memory_markup('Mem', 0, 0)))
        self.widgets.append(urwid.Text(self.memory_markup('Swp', 0, 0)))

        panel = urwid.Pile(self.widgets)
        urwid.WidgetWrap.__init__(self, panel)

    def refresh(self):
        """Update content of widget with actual data."""
        for i, value in enumerate(self.cpu.cpu_usage):
            self.widgets[i].set_text(self.cpu_markup(i + 1, value))

        self.widgets[-2].set_text(self.memory_markup('Mem', self.memory.used_memory, self.memory.total_memory))
        self.widgets[-1].set_text(self.memory_markup('Swp', self.memory.used_swap, self.memory.total_swap))

    def cpu_markup(self, index, percent, width=29):
        """Returns text markup for Text widget with CPU info"""
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

    def memory_markup(self, txt, used, total, width=24):
        """Returns text markup for Text widget with memory info"""
        used_mem = CpuAndMemoryPanel.format_memory(used)
        total_mem = CpuAndMemoryPanel.format_memory(total)

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
            ('cpu_pct', u'%5.5s/%5.5s' % (used_mem, total_mem)),
            ('progress_bracket', u']')
        ]

    @staticmethod
    def format_memory(value):
        """Return value as formatted string."""
        if value < 1024:
            result = '%4.4s%c' % (value, 'K')
        elif value < 1024*1024:
            result = '%4.4s%c' % (value/1024, 'M')
        elif value < 1024*1024*1024:
            result = '%4.4s%c' % (value/(1024*1024), 'G')
        return result


class RightPanel(urwid.WidgetWrap):
    """docstring for RightPanel"""
    def __init__(self, controller, uptime, load):
        self.controller = controller
        self.uptime = uptime
        self.load = load
        self.widgets = []

        self.widgets.append(urwid.Text([('fields_names', u' Tasks:'), ' 0, 0 thr, 0 kthr; 0 running']))
        self.widgets.append(urwid.Text([('fields_names', u' Load average:'), ' 0.0 0.0 0.0']))
        self.widgets.append(urwid.Text([('fields_names', u' Uptime:'), ' -- /-- ']))

        self.panel = urwid.Pile(self.widgets)
        urwid.WidgetWrap.__init__(self, self.panel)

    def refresh(self):
        self.widgets[0].set_text([('fields_names', u' Tasks:'), f' {self.controller.proccesses_number}, 0 thr, 0 kthr; {self.controller.running_proccesses_number} running'])
        self.widgets[1].set_text([('fields_names', u' Load average:'), self.load.load_average_as_string])
        self.widgets[2].set_text([('fields_names', u' Uptime:'), self.uptime.uptime_as_string])


class ProcessPanel(urwid.WidgetWrap):
    """docstring for ProcessPanel"""
    def __init__(self, controller):
        self.controller = controller
        self.header = urwid.Text(('table_header',u'  PID USER       PRI    NI VIRT   RES  SHR S  CPU%  MEM%      TIME+   Command'))

        self.processes = []

        for pr in self.controller.processes:
            self.processes.append(urwid.Text(self.process_markup(pr)))

        self.table_view = urwid.ListBox(urwid.SimpleFocusListWalker(self.processes))
        self.table_widget = urwid.Frame(self.table_view, header=self.header)

        urwid.WidgetWrap.__init__(self, self.table_widget)

    def refresh(self):
        self.processes = []

        for pr in self.controller.processes:
            self.processes.append(urwid.Text(self.process_markup(pr)))

    def process_markup(self, pr):
        priority = 'RT' if pr.priority == '-100' else pr.priority

        result = []
        result.append(('progress_bracket', u'%5.5s %-10.10s %4.4s' % (pr.pid, pr.user, priority)))

        if int(pr.niceness) < 0:
            result.append(('niceness', u' %4.4s' % pr.niceness))
        else:
            result.append(('progress_bracket', u' %4.4s' % pr.niceness))

        result.append(('progress_bracket', u' %4.4sM %4.4s %4.4s %1.1s  %4.1f  %4.1f %8.18s %s'
         % (pr.virtual_memory, pr.resident_memory, pr.shared_memory,
            pr.state, pr.cpu_usage, pr.memory_usage, pr.time, pr.command[:20])))

        return result


class Application:
    palette = [
        ('foot', 'black', 'dark cyan'),
        ('normal', 'white', ''),
        ('progress_bracket', 'white', ''),
        ('progress_bar', 'dark green', ''),
        ('cpu_pct', 'light gray', ''),
        ('fields_names', 'dark cyan', ''),
        ('table_header', 'black', 'dark green'),
        ('niceness', 'dark red', ''),
    ]

    def __init__(self):
        # initialize data sources
        self.cpu = Cpu()
        self.memory = MemInfo()
        self.uptime = Uptime()
        self.load = LoadAverage()
        self.processes = ProcessesController(self.uptime, self.memory.total_memory)
        self.refreshable_data = [self.cpu, self.memory, self.uptime, self.load, self.processes]

        # initialize buttons
        f1 = urwid.Button([('normal', u'F1'), ('foot', u'Help')])
        urwid.connect_signal(f1, 'click', self.handle_f1_buton)
        # f2 = urwid.Button([('normal', u'F2'), ('foot', u'Setup')])
        f3 = urwid.Button([('normal', u'F3'), ('foot', u'Search')])
        f4 = urwid.Button([('normal', u'F4'), ('foot', u'Filter')])
        # f5 = urwid.Button([('normal', u'F5'), ('foot', u'Tree')])
        f6 = urwid.Button([('normal', u'F6'), ('foot', u'SortBy')])
        f7 = urwid.Button([('normal', u'F7'), ('foot', u'Nice-')])
        f8 = urwid.Button([('normal', u'F8'), ('foot', u'Nice+')])
        # f9 = urwid.Button([('normal', u'F9'), ('foot', u'Kill')])
        f10 = urwid.Button([('normal', u'F10'), ('foot', u'Quit')])
        urwid.connect_signal(f10, 'click', self.handle_f10_buton)

        # initialize widgets
        self.left_panel = CpuAndMemoryPanel(self.cpu, self.memory)
        self.right_panel = RightPanel(self.processes, self.uptime, self.load)
        self.header = urwid.Columns([self.left_panel, self.right_panel])
        self.buttons = urwid.Columns([f1, f3, f4, f6, f7, f8, f10])
        self.processes_list = ProcessPanel(self.processes)
        self.main_widget = urwid.Frame(self.processes_list, header=self.header, footer=self.buttons)

        self.loop = urwid.MainLoop(self.main_widget,
                                    self.palette,
                                    unhandled_input=self.handle_input
                                    )

        self.loop.set_alarm_in(1, self.refresh)

    def refresh(self, loop, data):
        for i in self.refreshable_data:
            i.update()

        self.loop.set_alarm_in(1, self.refresh)
        self.left_panel.refresh()
        self.right_panel.refresh()
        # TODO(AOS) Update self.processes_list

    def start(self):
        self.loop.run()

    def handle_f1_buton(self, key):
        self.display_help()

    def handle_f2_buton(self, key):
        ...

    def handle_f3_buton(self, key):
        ...

    def handle_f4_buton(self, key):
        ...

    def handle_f5_buton(self, key):
        ...

    def handle_f6_buton(self, key):
        ...

    def handle_f7_buton(self, key):
        ...

    def handle_f8_buton(self, key):
        ...

    def handle_f9_buton(self, key):
        ...

    def handle_f10_buton(self, key):
        raise urwid.ExitMainLoop()

    def handle_input(self, key):
        if type(key) == str:
            if key in ('q', 'Q'):   #TODO(AOS) Remove in final version
                raise urwid.ExitMainLoop()
            if key == 'f1':
                self.display_help()
            else:
                self.loop.widget = self.main_widget
        elif type(key) == tuple:
            pass

    def display_help(self):
        help_txt = \
            f"""
        Pytop {__version__} - {__copyright__}
        Released under the {__license__}.

        Pytop is the htop copycat implemented in Python.

        usage: pytop [-h] [-v]

        optional arguments:
            -h, --help     show this help message and exit
            -v, --version  show program's version number and exit
        """
        self.help_txt = urwid.Text([('normal', help_txt),
                                    ('fields_names', u'\nPress any key to return')],
                                    align='left')
        fill = urwid.Filler(self.help_txt, 'top')
        self.loop.widget = fill


if __name__ == "__main__":
    options = parse_args()

    Application().start()
    sys.exit(0)