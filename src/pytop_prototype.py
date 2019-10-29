#!/usr/bin/env python3

""" pytop.py: Htop copycat implemented in Python. """
import datetime

__author__ = 'Andrii Oshtuk'
__copyright__ = '(C) 2019 ' + __author__
__license__ = "MIT"
__version__ = '0.0.1 Alpha 1'

import argparse
import os
import pwd


def parse_args():
    """ Returns script options parsed from CLI arguments."""
    argparser = argparse.ArgumentParser(prog='pytop')
    argparser.add_argument('-v', '--version', action='version',
                           version='%(prog)s ' + __version__ + ' - ' + __copyright__)
    argparser.add_argument("--limit", default=None, type=int,
                   help="Limit printed processes to N") #TODO(AOS) Remove in final version

    return argparser.parse_args()


class bcolors:
    ENDC = '\x1b[0m'
    HEADER = '\x1b[3;30;42m'

    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'

    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_process_cmdline(pid):
    """ Returns the command that originally started the process (content of /proc/PID/cmdline) """
    filename = f'/proc/{pid}/cmdline'
    with open(filename, 'r') as fcmd:
        return fcmd.read()


#TODO(AOS) Extract to some class below
def get_meminfo():
    MemTotal = MemFree = Buffers = Cached = SReclaimable = Shmem = SwapTotal = SwapFree = None
    with open('/proc/meminfo', 'r') as fstatus:
        for line in fstatus.readlines():
            if 'MemTotal:' in line:
                MemTotal = line.split()[1]
            elif 'MemFree:' in line:
                    MemFree = line.split()[1]
            elif 'Buffers:' in line:
                    Buffers = line.split()[1]
            elif 'Cached:' == line.split()[0]:
                    Cached = line.split()[1]
                    print('Cached:' + Cached)
            elif 'SReclaimable:' in line:
                    SReclaimable = line.split()[1]
            elif 'Shmem:' in line:
                    Shmem = line.split()[1]
            elif 'SwapTotal:' in line:
                    SwapTotal = line.split()[1]
            elif 'SwapFree:' in line:
                    SwapFree = line.split()[1]

            if MemTotal and MemFree and Buffers and Cached and SReclaimable and Shmem and SwapTotal and SwapFree:
                break

    return MemTotal, MemFree, Buffers, Cached, SReclaimable, Shmem, SwapTotal, SwapFree


def get_uptime():
    uptime = ' '
    with open('/proc/uptime', 'r') as fuptime:
        text = fuptime.read()
        uptime = text.split()[0]
    return uptime

def format_uptime(uptime):
    return str(datetime.timedelta(seconds=uptime))

def get_loadavg():
    loadavg = ' '
    with open('/proc/loadavg', 'r') as floadavg:
        text = floadavg.read().split()
        loadavg = ' '.join(text[:3])
    return loadavg


def get_threads_count():
    ...


def get_cpu_statistics():
    cpu_statistics = []
    for line in open('/proc/stat').readlines():
        cpu = {}
        if line.startswith('cpu '): continue
        if line.startswith('cpu'):
            line = line.split()
            cpu['user'] = int(line[1])
            cpu['nice'] = int(line[2])
            cpu['system'] = int(line[3])
            cpu['idle'] = int(line[4])
            cpu['iowait'] = int(line[5])
            cpu['irq'] = int(line[6])
            cpu['softirq'] = int(line[7])
            cpu['steal'] = int(line[8])
            cpu['guest'] = int(line[9])
            cpu['guest_nice'] = int(line[10])
            cpu_statistics.append(cpu)
    return cpu_statistics


cpu_stat_prev = None #TODO(AOS) Redo
def calculate_cpu_usage(init = False):
    global cpu_stat_prev
    cpu_usage = []

    if init:
        cpu_stat_prev = get_cpu_statistics()
        return

    cpu_stat = get_cpu_statistics()

    for (prev, new) in zip(cpu_stat_prev, cpu_stat):
        idle_prev = prev['idle'] + prev['iowait']
        idle_new = new['idle'] + new['iowait']

        non_idle_prev = prev['user'] + prev['nice'] + prev['system'] + prev['irq'] + prev['softirq'] + prev['steal']
        non_idle_new = new['user'] + new['nice'] + new['system'] + new['irq'] + new['softirq'] + new['steal']

        total_prev = idle_prev + non_idle_prev
        total_new = idle_new + non_idle_new

        total_diff = total_new - total_prev
        idle_diff = idle_new - idle_prev

        cpu_usage_pct = (total_diff-idle_diff)*100/total_diff
        cpu_usage.append(cpu_usage_pct)

    return cpu_usage


def get_process_state_and_virtmemory(pid):#TODO(AOS) Add user_name
    """ Returns the tuple (process_state, process_virtmemory)  (content of /proc/PID/status) """ #TODO(AOS) Add user_name
    filename = f'/proc/{pid}/status'
    process_state = ' '
    user_name = ' '
    process_vmsize = ' '
    process_vm_rss_size = ' '
    process_rss_file_size = ' '

    with open(filename, 'r') as fstatus:
        for line in fstatus.readlines():
            if 'State:' in line:
                process_state = line.split()[1]
            elif 'Uid:' in line:
                user_id = line.split()[1] #TODO(AOS) figure out whatever to use real or effective UID
                user_name = pwd.getpwuid(int(user_id)).pw_name
            elif 'VmSize:' in line:
                # process_vmsize = int(line.split()[1])/1024 #TODO(AOS) handles mB, kB properly
                vmsize = int(line.split()[1])
                process_vmsize = str(vmsize//1024)+'M' if vmsize > 1024 else str(vmsize)
                # process_vmsize = format(int(process_vmsize), 'd')
            elif 'VmRSS:' in line:
                process_vm_rss_size = line.split()[1] #TODO(AOS) Redo
                # print(process_vm_rss_size)
            elif 'RssFile:' in line:
                process_rss_file_size = line.split()[1] #TODO(AOS) Redo
    return (process_state, user_name, process_vmsize, process_vm_rss_size, process_rss_file_size)

def get_process_priority(pid):
    PF_KTHREAD = 0x00200000 #TODO(AOS) Redo

    filename = f'/proc/{pid}/stat'
    is_kthread = False
    process_priority = ' '
    process_niceness = ' '
    total_time_ticks = ' '
    start_time_ticks = ' '

    with open(filename, 'r') as fstatus:
        text = 'None '
        text = text + fstatus.read()
        is_kthread = True if int(text.split()[9]) & PF_KTHREAD else False
        process_priority = text.split()[18] #TODO(AOS) Why the heck are you calling split so many times?
        process_niceness = text.split()[19]
        total_time_ticks = str(int(text.split()[14]) + int(text.split()[15]) + int(text.split()[16]) + int(text.split()[17]))
        start_time_ticks = text.split()[22]
        process_time_ticks = str(int(text.split()[14]) + int(text.split()[15]))
    return (process_priority, process_niceness, total_time_ticks, start_time_ticks, process_time_ticks, is_kthread)

options = parse_args()

processes = [name for name in os.listdir("/proc") if os.path.isdir("/proc/" + name) and name.isdigit()]

if options.limit: #TODO(AOS) Remove in final version
    processes = processes[:options.limit]

MemTotal, MemFree, Buffers, Cached, SReclaimable, Shmem, SwapTotal, SwapFree = get_meminfo()

MemUsed = (int(MemTotal) - int(MemFree))/(1024*1024)
MemTotal = int(MemTotal)/(1024*1024)
Buffers = int(Buffers)/(1024*1024)
CachedMem = (int(Cached) + int(SReclaimable) - int(Shmem))/(1024*1024)
Green = MemUsed  - Buffers  - CachedMem

final_memory = f'(green):{Green}G Buffers (blue):{Buffers}G  Cached (yellow):{CachedMem}G {Green}G/{MemTotal}G'
print(final_memory)
print(SwapTotal + '/' + SwapFree)

d = input('check memory')

clock_ticks_per_second = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

header = bcolors.HEADER + '  PID USER        PRI  NI  VIRT   RES   SHR S CPU% MEM%    TIME+ Command' + bcolors.ENDC
print(header)
total_kthread = 0

for process in processes:
    pid_str = format(process, '>5s')
    cmdline = get_process_cmdline(process)
    process_state, user_name, process_vmsize, process_vm_rss_size, process_rss_file_size = get_process_state_and_virtmemory(process)
    process_priority, process_niceness, total_time_ticks, start_time_ticks, process_time_ticks, is_kthread = get_process_priority(process)

    if is_kthread: total_kthread += 1

    if process_vm_rss_size != ' ':
        # mem_percent = str(int(process_vm_rss_size)*100/int(MemTotal))
        mem_percent = format(int(process_vm_rss_size)*100/int(MemTotal), '.1f')
    else:
        mem_percent = ' '

    uptime = get_uptime()

    seconds = float(uptime) - (int(start_time_ticks)/clock_ticks_per_second)
    cpu_percent = format(100 * ((int(total_time_ticks)/clock_ticks_per_second)/seconds), '.1f')

    process_time = format(float(process_time_ticks)/clock_ticks_per_second, '.2f') #TODO(AOS) Add proper format as HH:SS.XX

    final_row = ' '.join([pid_str, user_name, process_priority, process_niceness, process_vmsize, process_vm_rss_size,
                          process_rss_file_size, process_state, cpu_percent, mem_percent, process_time, cmdline[:100]])
    # print(pid_str + process_state + process_vmsize + ' ' *30 + cmdline[:100]) #TODO(AOS) Handle long cmdline later
    print(final_row)
