from unittest.mock import patch, mock_open
from src.sysinfo import Cpu, SystemInfoError, LoadAverage, Uptime, MemInfo, Process
import pytest
from distutils.dir_util import copy_tree
import os


@pytest.fixture()
def read_file():
    def _read_file(name):
        with open(name) as f:
            return f.read()
    return _read_file

class TestCpu:

    usage_vs_files = [
        (0.0, 'tests/test_sysinfo/010_proc_stat_usage_0_pct'),
        (25.0, 'tests/test_sysinfo/011_proc_stat_usage_25_pct'),
        (50.0, 'tests/test_sysinfo/012_proc_stat_usage_50_pct'),
        (75.0, 'tests/test_sysinfo/013_proc_stat_usage_75_pct'),
        (100.0, 'tests/test_sysinfo/014_proc_stat_usage_100_pct'),
    ]

    def test_create_cpu_obj(self, read_file):
        data = read_file('tests/test_sysinfo/001_proc_stat')
        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            cpu = Cpu()
            assert cpu.cpu_usage == [0.0, 0.0, 0.0, 0.0]
            mock_file.assert_called_with("/proc/stat")

    def test_no_file(self):
        with pytest.raises(OSError):
            with patch('builtins.open') as mock_open:
                mock_open.side_effect = OSError
                cpu = Cpu()

    def test_create_1cpu_obj(self, read_file):
        data = read_file('tests/test_sysinfo/003_proc_stat_1_cpu')
        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            cpu = Cpu()
            assert cpu.cpu_usage == [0.0]
            mock_file.assert_called_with("/proc/stat")

    def test_create_32cpu_obj(self, read_file):
        data = read_file('tests/test_sysinfo/002_proc_stat_32_cpu')
        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            cpu = Cpu()
            assert cpu.cpu_usage == [0.0] * 32
            mock_file.assert_called_with("/proc/stat")

    def test_wrong_format(self, read_file):
        data = read_file('tests/test_sysinfo/004_proc_stat_wrong_format')
        with pytest.raises(SystemInfoError) as ex:
            with patch("builtins.open", mock_open(read_data=data)) as mock_file:
                cpu = Cpu()

        assert str(ex.value) == 'Cannot parse /proc/stat file'

    @pytest.mark.parametrize('expected, filename', usage_vs_files)
    def test_cpu_usage_n_pct(self, read_file, expected, filename):
        data = read_file('tests/test_sysinfo/001_proc_stat')
        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            cpu = Cpu()
            mock_file.assert_called_with("/proc/stat")

        data = read_file(filename)
        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            cpu.update()
            assert cpu.cpu_usage == [expected] * 4
            mock_file.assert_called_with("/proc/stat")


class TestLoadAverage:
    result_vs_files = [
        ((0.63, 0.41, 0.77), 'tests/test_sysinfo/020_loadavg'),
        ((0.0, 0.5, 2.0), 'tests/test_sysinfo/021_loadavg'),
        ((4.0, 4.5, 4.0), 'tests/test_sysinfo/022_loadavg'),
    ]

    result_str_vs_files = [
        ('0.63 0.41 0.77', 'tests/test_sysinfo/020_loadavg'),
        ('0.0 0.5 2.0', 'tests/test_sysinfo/021_loadavg'),
        ('4.0 4.5 4.0', 'tests/test_sysinfo/022_loadavg'),
    ]

    wrong_format_files = [
        'tests/test_sysinfo/023_loadavg_wrong_format',
        'tests/test_sysinfo/024_loadavg_wrong_format',
    ]

    def test_no_file(self):
        with pytest.raises(OSError):
            with patch('builtins.open') as mock_open:
                mock_open.side_effect = OSError
                loadavg = LoadAverage()

    @pytest.mark.parametrize('filename', wrong_format_files)
    def test_wrong_format(self, read_file, filename):
        data = read_file(filename)
        with pytest.raises(SystemInfoError) as ex:
            with patch("builtins.open", mock_open(read_data=data)) as mock_file:
                loadavg = LoadAverage()

        assert str(ex.value) == 'Cannot parse /proc/loadavg file'

    @pytest.mark.parametrize('expected, filename', result_vs_files)
    def test_load_average(self, read_file, expected, filename):
        data = read_file(filename)
        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            loadavg = LoadAverage()
            assert loadavg.load_average == expected
            mock_file.assert_called_with("/proc/loadavg")

    @pytest.mark.parametrize('expected, filename', result_str_vs_files)
    def test_load_average_as_string(self, read_file, expected, filename):
        data = read_file(filename)
        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            loadavg = LoadAverage()
            assert loadavg.load_average_as_string == expected
            mock_file.assert_called_with("/proc/loadavg")


class TestUptime:

    # TODO(AOS) Create test data files in fixture instead of static files

    result_vs_files = [
        (721736, 'tests/test_sysinfo/030_uptime'),
        (86400, 'tests/test_sysinfo/031_uptime'),
        (30844800, 'tests/test_sysinfo/032_uptime'),
        (115230, 'tests/test_sysinfo/033_uptime'),
    ]

    result_str_vs_files = [
        ('8 days, 8:28:56', 'tests/test_sysinfo/030_uptime'),
        ('1 day, 0:00:00', 'tests/test_sysinfo/031_uptime'),
        ('357 days, 0:00:00', 'tests/test_sysinfo/032_uptime'),
        ('1 day, 8:00:30', 'tests/test_sysinfo/033_uptime'),
    ]

    wrong_format_files = [
        'tests/test_sysinfo/034_uptime_wrong_format',
        'tests/test_sysinfo/035_uptime_wrong_format',
        'tests/test_sysinfo/036_uptime_wrong_format',
    ]

    def test_no_file(self):
        with pytest.raises(OSError):
            with patch('builtins.open') as mock_open:
                mock_open.side_effect = OSError
                uptime = Uptime()

    @pytest.mark.parametrize('filename', wrong_format_files)
    def test_wrong_format(self, read_file, filename):
        data = read_file(filename)
        with pytest.raises(SystemInfoError) as ex:
            with patch("builtins.open", mock_open(read_data=data)) as mock_file:
                uptime = Uptime()

        assert str(ex.value) == 'Cannot parse /proc/uptime file'

    @pytest.mark.parametrize('expected, filename', result_vs_files)
    def test_load_average(self, read_file, expected, filename):
        data = read_file(filename)
        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            uptime = Uptime()
            assert uptime.uptime == expected
            mock_file.assert_called_with("/proc/uptime")

    @pytest.mark.parametrize('expected, filename', result_str_vs_files)
    def test_load_average_as_string(self, read_file, expected, filename):
        data = read_file(filename)
        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            uptime = Uptime()
            assert uptime.uptime_as_string == expected
            mock_file.assert_called_with("/proc/uptime")


class TestMemInfo:

    result_vs_files = [
        ((7779304, 5316848, 2097148, 1944256), 'tests/test_sysinfo/041_meminfo'),
        ((16777216, 6803696, 6291456, 0), 'tests/test_sysinfo/042_meminfo'),
        ((16777216, 14583000, 6291456, 6291456), 'tests/test_sysinfo/043_meminfo'),
    ]

    wrong_format_files = [
        'tests/test_sysinfo/045_meminfo_wrong_format',
        'tests/test_sysinfo/046_meminfo_wrong_format',
        'tests/test_sysinfo/047_meminfo_wrong_format',
        'tests/test_sysinfo/048_meminfo_wrong_format',
    ]

    def test_no_file(self):
        with pytest.raises(OSError):
            with patch('builtins.open') as mock_open:
                mock_open.side_effect = OSError
                uptime = MemInfo()

    @pytest.mark.parametrize('filename', wrong_format_files)
    def test_wrong_format(self, read_file, filename):
        data = read_file(filename)
        with pytest.raises(SystemInfoError) as ex:
            with patch("builtins.open", mock_open(read_data=data)) as mock_file:
                memory = MemInfo()

        assert str(ex.value) == 'Cannot parse /proc/meminfo file'

    @pytest.mark.parametrize('expected, filename', result_vs_files)
    def test_memory_info(self, read_file, expected, filename):
        data = read_file(filename)
        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            memory = MemInfo()
            assert memory.total_memory == expected[0]
            assert memory.used_memory == expected[1]
            assert memory.total_swap == expected[2]
            assert memory.used_swap == expected[3]
            mock_file.assert_called_with("/proc/meminfo")


class TestProcess:

    process1 = {'pid':'1', 'user':'root', 'priority':'20', 'niceness':'0', 'virtual_memory':'220M',
                'resident_memory':'5248', 'shared_memory':'3384', 'state':'S', 'cpu_usage':'0.0',
                'memory_usage':'0.1', 'time':'0:14.76', 'command':'/sbin/init splash',
    }

    process4 = {'pid': '4', 'user': 'root', 'priority': '20', 'niceness': '-20', 'virtual_memory': '0',
                'resident_memory': '0', 'shared_memory': '0', 'state': 'I', 'cpu_usage': '0.0',
                'memory_usage': '0.0', 'time': '0:00.00', 'command': 'kworker/0:0H',
                }

    process1051 = {'pid': '1051', 'user': 'test_user', 'priority': '11', 'niceness': '22', 'virtual_memory': '96G',
                'resident_memory': '1000M', 'shared_memory': '13504', 'state': 'S', 'cpu_usage': '100.0',
                'memory_usage': '100.0', 'time': '5h50.16', 'command': 'test comand line',
                }

    result_vs_pid = [
        (process1, 1),
        (process4, 4),
        (process1051, 1051),
    ]

    wrong_format_pid = [
        400,
        401,
        402,
        # 403,
    ]

    @pytest.fixture(params=wrong_format_pid)
    # @pytest.mark.parametrize('pid', wrong_format_pid)
    def get_process_wrong_format(tmpdir, request):
        pid = request.param
        dir_path = os.path.dirname(os.path.realpath(__file__))
        process_folder = os.path.join(dir_path, 'test_sysinfo', str(pid))
        temporary_folder = os.path.join(str(tmpdir), str(pid))
        copy_tree(process_folder, temporary_folder)
        Process._proc_folder = temporary_folder
        process = Process(pid)
        return process

    @pytest.fixture(params=result_vs_pid)
    # @pytest.mark.parametrize('expected, pid', result_vs_pid)
    def get_process(tmpdir, request):
        expected, pid = request.param

        dir_path = os.path.dirname(os.path.realpath(__file__))
        process_folder = os.path.join(dir_path, 'test_sysinfo', str(pid))
        temporary_folder = os.path.join(str(tmpdir), str(pid))
        copy_tree(process_folder, temporary_folder)
        Process._proc_folder = temporary_folder
        process = Process(pid)
        return expected, process

    def test_no_file(self):
        with pytest.raises(OSError):
            Process._proc_folder = os.path.dirname(os.path.realpath(__file__))
            process = Process(1)

    def test_no_folder(self):
        with pytest.raises(OSError):
            Process._proc_folder = '/homehome'
            process = Process(1)

    def test_wrong_format(self, get_process_wrong_format):
        with pytest.raises(SystemInfoError) as ex:
            get_process_wrong_format()

    def test_pid(self, get_process):
        expected, actual = get_process
        assert actual.pid == expected['pid']

    def test_user(self, get_process):
        expected, actual = get_process
        assert actual.user == expected['user']

    def test_priority(self, get_process):
        expected, actual = get_process
        assert actual.priority == expected['priority']

    def test_niceness(self, get_process):
        expected, actual = get_process
        assert actual.niceness == expected['niceness']

    def test_virtual_memory(self, get_process):
        expected, actual = get_process
        assert actual.virtual_memory == expected['virtual_memory']

    def test_resident_memory(self, get_process):
        expected, actual = get_process
        assert actual.resident_memory == expected['resident_memory']

    def test_shared_memory(self, get_process):
        expected, actual = get_process
        assert actual.resident_memory == expected['shared_memory']

    def test_state(self, get_process):
        expected, actual = get_process
        assert actual.resident_memory == expected['state']

    def test_cpu_usage(self, get_process):
        expected, actual = get_process
        assert actual.resident_memory == expected['cpu_usage']

    def test_memory_usage(self, get_process):
        expected, actual = get_process
        assert actual.resident_memory == expected['memory_usage']

    def test_time(self, get_process):
        expected, actual = get_process
        assert actual.resident_memory == expected['time']

    def test_command(self, get_process):
        expected, actual = get_process
        assert actual.command == expected['command']
