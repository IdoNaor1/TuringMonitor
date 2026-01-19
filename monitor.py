"""
System Monitor Module
Collects system metrics using psutil
"""

import psutil
from datetime import datetime
import socket
import platform
from data_history import DataHistory
from external_data import ExternalDataManager


def get_cpu_usage():
    """
    Get current CPU usage percentage

    Returns:
        float: CPU usage percentage (0-100)
    """
    return psutil.cpu_percent(interval=0.1)


def get_ram_usage():
    """
    Get current RAM usage information

    Returns:
        dict: Dictionary containing:
            - used: Used RAM in GB
            - total: Total RAM in GB
            - percent: Usage percentage (0-100)
    """
    mem = psutil.virtual_memory()
    return {
        'used': mem.used / (1024 ** 3),  # Convert to GB
        'total': mem.total / (1024 ** 3),  # Convert to GB
        'percent': mem.percent
    }


def get_current_time(format_str="%H:%M:%S"):
    """
    Get current system time

    Args:
        format_str: Time format string (default: HH:MM:SS)

    Returns:
        str: Formatted time string
    """
    return datetime.now().strftime(format_str)


def get_disk_usage():
    """
    Get C: drive usage information

    Returns:
        dict: Dictionary containing:
            - used: Used disk space in GB
            - total: Total disk space in GB
            - percent: Usage percentage (0-100)
    """
    disk = psutil.disk_usage('C:\\')
    return {
        'used': disk.used / (1024 ** 3),  # Convert to GB
        'total': disk.total / (1024 ** 3),  # Convert to GB
        'percent': disk.percent
    }


def get_gpu_usage():
    """
    Get GPU usage information (NVIDIA GPUs only)

    Returns:
        dict or None: Dictionary containing GPU metrics if available:
            - gpu_percent: GPU usage percentage (0-100)
            - gpu_memory_percent: GPU memory usage percentage (0-100)
            - gpu_temp: GPU temperature in Celsius
            - gpu_name: GPU model name
        Returns None if no GPU available or GPUtil not installed
    """
    try:
        # Suppress console windows on Windows when GPUtil spawns subprocesses
        import sys
        if sys.platform == 'win32':
            import subprocess
            # Store original CREATE_NO_WINDOW flag
            CREATE_NO_WINDOW = 0x08000000
            # Monkey-patch subprocess to hide console windows
            old_popen = subprocess.Popen.__init__
            def new_popen(self, *args, **kwargs):
                kwargs.setdefault('creationflags', 0)
                kwargs['creationflags'] |= CREATE_NO_WINDOW
                old_popen(self, *args, **kwargs)
            subprocess.Popen.__init__ = new_popen

        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]  # Primary GPU
            return {
                'gpu_percent': gpu.load * 100,
                'gpu_memory_percent': gpu.memoryUtil * 100,
                'gpu_temp': gpu.temperature,
                'gpu_name': gpu.name
            }
    except (ImportError, Exception):
        pass
    return None


def get_cpu_name():
    """
    Get CPU model name via WMI on Windows

    Returns:
        str: CPU model name (e.g., "Intel Core i7-12700K") or generic name
    """
    try:
        import wmi
        c = wmi.WMI()
        for processor in c.Win32_Processor():
            return processor.Name.strip()
    except:
        # Fallback to platform.processor() if WMI fails
        proc_name = platform.processor()
        if proc_name:
            return proc_name
        return "Unknown CPU"


def get_component_temperatures():
    """
    Get all available temperature sensors

    Returns:
        dict: Dictionary of temperature readings (empty if none available)
              Keys are sensor names, values are temperatures in Celsius
    """
    temps = {}
    try:
        temps_info = psutil.sensors_temperatures()
        if temps_info:
            for name, entries in temps_info.items():
                for entry in entries:
                    # Create unique key for each sensor
                    if entry.label:
                        key = f"{name}_{entry.label}"
                    else:
                        key = name
                    temps[key] = entry.current
    except (AttributeError, Exception):
        # sensors_temperatures() not available on all platforms
        pass
    return temps


# Global network counter storage for speed calculation
_last_net_io = None
_last_net_time = None

# Global disk I/O counter storage for speed calculation
_last_disk_io = None
_last_disk_io_time = None

# Global historical data manager for sparklines
_data_history = DataHistory(max_points=30)

# Global external data manager
_external_data_manager = ExternalDataManager()


def get_network_speed():
    """
    Get current network upload/download speed

    Returns:
        dict: Dictionary containing:
            - upload_kbs: Upload speed in KB/s
            - download_kbs: Download speed in KB/s
            - upload_mbs: Upload speed in MB/s
            - download_mbs: Download speed in MB/s
    """
    global _last_net_io, _last_net_time

    try:
        import time
        current_io = psutil.net_io_counters()
        current_time = time.time()

        if _last_net_io is None or _last_net_time is None:
            # First call - initialize counters
            _last_net_io = current_io
            _last_net_time = current_time
            return {
                'upload_kbs': 0.0,
                'download_kbs': 0.0,
                'upload_mbs': 0.0,
                'download_mbs': 0.0
            }

        # Calculate time delta
        time_delta = current_time - _last_net_time
        if time_delta == 0:
            return {
                'upload_kbs': 0.0,
                'download_kbs': 0.0,
                'upload_mbs': 0.0,
                'download_mbs': 0.0
            }

        # Calculate bytes transferred
        bytes_sent = current_io.bytes_sent - _last_net_io.bytes_sent
        bytes_recv = current_io.bytes_recv - _last_net_io.bytes_recv

        # Calculate speeds in KB/s
        upload_kbs = (bytes_sent / time_delta) / 1024
        download_kbs = (bytes_recv / time_delta) / 1024

        # Update stored values
        _last_net_io = current_io
        _last_net_time = current_time

        return {
            'upload_kbs': upload_kbs,
            'download_kbs': download_kbs,
            'upload_mbs': upload_kbs / 1024,
            'download_mbs': download_kbs / 1024
        }
    except Exception:
        return {
            'upload_kbs': 0.0,
            'download_kbs': 0.0,
            'upload_mbs': 0.0,
            'download_mbs': 0.0
        }


def format_uptime():
    """
    Get system uptime as formatted string

    Returns:
        str: Uptime formatted as "Xd Xh Xm" (e.g., "2d 5h 23m")
    """
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m"
    except Exception:
        return "0d 0h 0m"


def get_cpu_frequency():
    """
    Get CPU frequency details

    Returns:
        dict: Dictionary containing:
            - cpu_freq_mhz: Current frequency in MHz (0 if unavailable)
            - cpu_freq_ghz: Current frequency in GHz (0 if unavailable)
    """
    try:
        freq = psutil.cpu_freq()
        if freq:
            return {
                'cpu_freq_mhz': round(freq.current, 1),
                'cpu_freq_ghz': round(freq.current / 1000, 2)
            }
    except (AttributeError, NotImplementedError):
        pass
    return {'cpu_freq_mhz': 0, 'cpu_freq_ghz': 0}


def get_per_core_cpu():
    """
    Get per-core CPU usage

    Returns:
        dict: Dictionary containing:
            - cpu_core_0, cpu_core_1, etc.: Individual core percentages
            - cpu_core_count: Number of CPU cores
            - cpu_cores_avg: Average CPU usage across all cores
    """
    try:
        per_cpu = psutil.cpu_percent(percpu=True, interval=0.1)
        result = {}
        for i, usage in enumerate(per_cpu):
            result[f'cpu_core_{i}'] = round(usage, 1)
        result['cpu_core_count'] = len(per_cpu)
        result['cpu_cores_avg'] = round(sum(per_cpu) / len(per_cpu), 1)
        return result
    except Exception:
        return {}


def get_disk_io_speed():
    """
    Calculate disk read/write speeds in MB/s and KB/s

    Returns:
        dict: Dictionary containing:
            - disk_read_mbs: Read speed in MB/s
            - disk_write_mbs: Write speed in MB/s
            - disk_read_kbs: Read speed in KB/s
            - disk_write_kbs: Write speed in KB/s
    """
    global _last_disk_io, _last_disk_io_time

    try:
        import time
        current_io = psutil.disk_io_counters()
        current_time = time.time()

        if _last_disk_io is None or _last_disk_io_time is None:
            # First call - initialize counters
            _last_disk_io = current_io
            _last_disk_io_time = current_time
            return {
                'disk_read_mbs': 0.0,
                'disk_write_mbs': 0.0,
                'disk_read_kbs': 0.0,
                'disk_write_kbs': 0.0
            }

        # Calculate time delta
        time_delta = current_time - _last_disk_io_time
        if time_delta == 0:
            return {
                'disk_read_mbs': 0.0,
                'disk_write_mbs': 0.0,
                'disk_read_kbs': 0.0,
                'disk_write_kbs': 0.0
            }

        # Calculate bytes transferred
        bytes_read = current_io.read_bytes - _last_disk_io.read_bytes
        bytes_write = current_io.write_bytes - _last_disk_io.write_bytes

        # Calculate speeds
        read_mbs = (bytes_read / time_delta) / (1024 * 1024)
        write_mbs = (bytes_write / time_delta) / (1024 * 1024)

        # Update stored values
        _last_disk_io = current_io
        _last_disk_io_time = current_time

        return {
            'disk_read_mbs': round(read_mbs, 2),
            'disk_write_mbs': round(write_mbs, 2),
            'disk_read_kbs': round(read_mbs * 1024, 1),
            'disk_write_kbs': round(write_mbs * 1024, 1)
        }
    except Exception:
        return {
            'disk_read_mbs': 0.0,
            'disk_write_mbs': 0.0,
            'disk_read_kbs': 0.0,
            'disk_write_kbs': 0.0
        }


def get_all_metrics():
    """
    Get all system metrics in a single call

    Returns:
        dict: Dictionary containing all metrics:
            - cpu_percent: CPU usage (%)
            - cpu_name: CPU model name
            - cpu_freq_mhz: CPU frequency in MHz
            - cpu_freq_ghz: CPU frequency in GHz
            - cpu_core_0, cpu_core_1, etc.: Per-core CPU usage (%)
            - cpu_core_count: Number of CPU cores
            - ram_used: RAM used (GB)
            - ram_total: RAM total (GB)
            - ram_percent: RAM usage (%)
            - time: Current time string
            - date: Current date string (format: "Sat, Jan 18")
            - disk_c_used: C: drive used (GB)
            - disk_c_total: C: drive total (GB)
            - disk_c_percent: C: drive usage (%)
            - disk_read_mbs: Disk read speed (MB/s)
            - disk_write_mbs: Disk write speed (MB/s)
            - disk_read_kbs: Disk read speed (KB/s)
            - disk_write_kbs: Disk write speed (KB/s)
            - gpu_percent: GPU usage (%) - 0 if unavailable
            - gpu_memory_percent: GPU memory usage (%) - 0 if unavailable
            - gpu_temp: GPU temperature (°C) - 0 if unavailable
            - gpu_name: GPU model name - "N/A" if unavailable
            - cpu_temp: CPU temperature (°C) - 0 if unavailable
            - temp_{sensor_name}: All available temperature sensors
            - net_upload_kbs: Network upload speed (KB/s)
            - net_download_kbs: Network download speed (KB/s)
            - net_upload_mbs: Network upload speed (MB/s)
            - net_download_mbs: Network download speed (MB/s)
            - uptime: System uptime formatted string
            - hostname: System hostname
    """
    ram = get_ram_usage()
    disk = get_disk_usage()
    gpu = get_gpu_usage()
    network = get_network_speed()
    temps = get_component_temperatures()
    cpu_freq = get_cpu_frequency()
    per_core = get_per_core_cpu()
    disk_io = get_disk_io_speed()

    metrics = {
        'cpu_percent': get_cpu_usage(),
        'cpu_name': 'Intel core i7-14700',  # Static name for CPU
        'ram_used': ram['used'],
        'ram_total': ram['total'],
        'ram_percent': ram['percent'],
        'ram_name': 'XPG Lancer DDR5 6400MHz',  # Generic name for RAM
        'time': get_current_time(),
        'date': datetime.now().strftime('%a, %b %d'),
        'disk_c_used': disk['used'],
        'disk_c_total': disk['total'],
        'disk_c_percent': disk['percent'],
        'disk_name': 'Samsung SSD 990 PRO 2TB',  # Example static name

        # Network speeds
        'net_upload_kbs': network['upload_kbs'],
        'net_download_kbs': network['download_kbs'],
        'net_upload_mbs': network['upload_mbs'],
        'net_download_mbs': network['download_mbs'],
        # System info
        'uptime': format_uptime(),
        'hostname': socket.gethostname()
    }

    # Add CPU frequency metrics
    metrics.update(cpu_freq)

    # Add per-core CPU metrics
    metrics.update(per_core)

    # Add disk I/O speeds
    metrics.update(disk_io)

    # Add GPU metrics if available
    if gpu:
        metrics.update({
            'gpu_percent': gpu['gpu_percent'],
            'gpu_memory_percent': gpu['gpu_memory_percent'],
            'gpu_temp': gpu['gpu_temp'],
            'gpu_name': gpu['gpu_name']
        })
    else:
        # Default values when GPU not available
        metrics.update({
            'gpu_percent': 0,
            'gpu_memory_percent': 0,
            'gpu_temp': 0,
            'gpu_name': 'N/A'
        })

    # Add CPU temperature if available
    cpu_temp = 0
    for key, value in temps.items():
        # Look for CPU temperature sensors (varies by platform)
        if any(keyword in key.lower() for keyword in ['coretemp', 'cpu', 'k10temp', 'zenpower']):
            cpu_temp = value
            break
    metrics['cpu_temp'] = cpu_temp

    # Expose all temperature sensors as data sources
    for sensor_name, temp_value in temps.items():
        # Sanitize sensor name for use as data source key
        clean_name = sensor_name.lower().replace(' ', '_').replace('-', '_')
        metrics[f'temp_{clean_name}'] = round(temp_value, 1)

    # Record historical data for sparkline-enabled metrics
    # Core metrics
    _data_history.add_data_point('cpu_percent', metrics['cpu_percent'])
    _data_history.add_data_point('ram_percent', metrics['ram_percent'])
    _data_history.add_data_point('ram_used', metrics['ram_used'])
    _data_history.add_data_point('ram_total', metrics['ram_total'])
    _data_history.add_data_point('gpu_percent', metrics['gpu_percent'])
    _data_history.add_data_point('gpu_memory_percent', metrics['gpu_memory_percent'])
    
    # Network
    _data_history.add_data_point('net_upload_mbs', metrics['net_upload_mbs'])
    _data_history.add_data_point('net_download_mbs', metrics['net_download_mbs'])
    _data_history.add_data_point('net_upload_kbs', metrics['net_upload_kbs'])
    _data_history.add_data_point('net_download_kbs', metrics['net_download_kbs'])
    
    # Disk
    _data_history.add_data_point('disk_read_mbs', metrics['disk_read_mbs'])
    _data_history.add_data_point('disk_write_mbs', metrics['disk_write_mbs'])
    _data_history.add_data_point('disk_c_percent', metrics['disk_c_percent'])
    
    # CPU frequency and per-core (if available)
    if 'cpu_freq_mhz' in metrics:
        _data_history.add_data_point('cpu_freq_mhz', metrics['cpu_freq_mhz'])
        _data_history.add_data_point('cpu_freq_ghz', metrics['cpu_freq_ghz'])
    
    # Per-core CPU (track up to 16 cores)
    for i in range(16):
        core_key = f'cpu_core_{i}'
        if core_key in metrics:
            _data_history.add_data_point(core_key, metrics[core_key])
    
    if 'cpu_cores_avg' in metrics:
        _data_history.add_data_point('cpu_cores_avg', metrics['cpu_cores_avg'])
    
    # Temperatures
    if metrics['cpu_temp'] > 0:
        _data_history.add_data_point('cpu_temp', metrics['cpu_temp'])
    if metrics['gpu_temp'] > 0:
        _data_history.add_data_point('gpu_temp', metrics['gpu_temp'])
    
    # All temperature sensors
    for key, value in metrics.items():
        if key.startswith('temp_') and isinstance(value, (int, float)):
            _data_history.add_data_point(key, value)

    # Add external data if available
    external_data = _external_data_manager.get_data()
    metrics.update(external_data)
    
    # Track external data for sparklines (weather, stocks, crypto)
    for key, value in external_data.items():
        if isinstance(value, (int, float)):
            _data_history.add_data_point(key, value)

    return metrics


def get_data_history(metric_name, num_points=30):
    """
    Public API for widgets to access historical data

    Args:
        metric_name: Name of metric (e.g., 'gpu_percent')
        num_points: Number of recent points to return (default: 30)

    Returns:
        list: List of values (empty if metric not found)
    """
    return _data_history.get_history(metric_name, num_points)


def initialize_external_data(config):
    """
    Initialize and start external data fetching

    Args:
        config: Dictionary with external data configuration
                (weather, stocks, crypto settings)
    """
    _external_data_manager.configure(config)
    _external_data_manager.start()


def stop_external_data():
    """Stop external data fetching"""
    _external_data_manager.stop()


# For testing
if __name__ == "__main__":
    print("System Metrics Test")
    print("=" * 50)

    metrics = get_all_metrics()

    print(f"Time: {metrics['time']}")
    print(f"Date: {metrics['date']}")
    print(f"Hostname: {metrics['hostname']}")
    print(f"Uptime: {metrics['uptime']}")
    print()
    print(f"CPU: {metrics['cpu_name']}")
    print(f"CPU Usage: {metrics['cpu_percent']:.1f}%")
    print(f"CPU Temp: {metrics['cpu_temp']:.1f}°C")
    print()
    print(f"RAM Usage: {metrics['ram_used']:.2f} GB / {metrics['ram_total']:.2f} GB ({metrics['ram_percent']:.1f}%)")
    print()
    print(f"C: Drive: {metrics['disk_c_used']:.2f} GB / {metrics['disk_c_total']:.2f} GB ({metrics['disk_c_percent']:.1f}%)")
    print()
    print(f"GPU: {metrics['gpu_name']}")
    print(f"GPU Usage: {metrics['gpu_percent']:.1f}%")
    print(f"GPU Memory: {metrics['gpu_memory_percent']:.1f}%")
    print(f"GPU Temp: {metrics['gpu_temp']:.0f}°C")
    print()
    print(f"Network Upload: {metrics['net_upload_kbs']:.2f} KB/s ({metrics['net_upload_mbs']:.3f} MB/s)")
    print(f"Network Download: {metrics['net_download_kbs']:.2f} KB/s ({metrics['net_download_mbs']:.3f} MB/s)")
