#!/usr/bin/env python3

""" pytop.py: Htop copycat implemented in Python. """

__author__ = 'Andrii Oshtuk'
__copyright__ = '(C) 2019 ' + __author__
__license__ = "MIT"
__version__ = '1.0.0'

import urwid
import argparse

from src.sysinfo import Cpu, MemInfo, Uptime, LoadAverage, ProcessesController


def parse_args():
    """ Returns script options parsed from CLI arguments."""
    argparser = argparse.ArgumentParser(prog='pytop')
    argparser.add_argument('-v', '--version', action='version',
                           version='%(prog)s ' + __version__ + ' - ' + __copyright__)

    return argparser.parse_args()


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
        for i in self.data:
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