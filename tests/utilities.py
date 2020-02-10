from collections import namedtuple

# CpuStat = namedtuple('CpuStat',
#                          ['name', 'user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest',
#                           'guest_nice'])
#
# lst = []
# with open('test_sysinfo/001_proc_stat') as f:
#     for line in f:
#         if line.startswith('cpu '):
#             continue
#         elif line.startswith('cpu'):
#             values = map(int, line.split()[1:])
#             temp = CpuStat(line.split()[0], *values)
#             lst.append(temp)
#
# for usage in range(0, 101, 25):
#     usage =25
#     base = 1000
#     idle = base * (100-usage)/100.0
#     busy = base - idle
#
#     temp1 = int(idle/2)
#
#     reminder = 0
#     while busy%6:
#         reminder += 1
#         busy -= 1
#
#     temp2 = int(busy / 6)
#
#     print(reminder)
#
#     print(f'\n usage={usage}%')
#
#     for l in lst:
#         print(f'{l.name} {l.user+temp2} {l.nice+temp2} {l.system+temp2} {l.idle+temp1} {l.iowait+temp1} {l.irq+temp2} '
#               f'{l.softirq+temp2+reminder} {l.steal+temp2} {l.guest} {l.guest_nice}')

def calculate_meminfo():
    # with open('/proc/meminfo') as f:
    with open('test_sysinfo/043_meminfo') as f:
        values = {}
        for line in f:
            field, value, *temp = line.split()
            values[field[:-1]] = value

    total = int(values["MemTotal"])
    print(f'MemTotal = {total}')
    free = values["MemFree"]
    print(f'Free = {free}')

    cached = int(values["Cached"]) + int(values["SReclaimable"]) - int(values["Shmem"])
    print(f'Cached = {cached}')
    buffers = int(values["Buffers"])
    print(f'Buffers = {buffers}')
    print(f'buff/cache = {cached + buffers}')

    used_memory = int(values["MemTotal"]) - int(values["MemFree"]) - buffers - cached
    print(f'Used_memory = {used_memory}')

    swap_total = int(values["SwapTotal"])
    print(f'SwapTotal = {swap_total}')
    swap_used = swap_total - int(values["SwapFree"])
    print(f'SwapFree = {swap_used}')

    print(f'\nTuple = ({total}, {used_memory}, {swap_total}, {swap_used})')

calculate_meminfo()