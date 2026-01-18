"""
Extended System Monitor Module
Collects comprehensive system metrics including disk, network, temps
"""

import psutil
from datetime import datetime
import platform


def get_cpu_usage():
    """Get CPU usage percentage"""
    return psutil.cpu_percent(interval=0.1)


def get_cpu_per_core():
    """Get per-core CPU usage"""
    return psutil.cpu_percent(interval=0.1, percpu=True)


def get_cpu_freq():
    """Get CPU frequency"""
    freq = psutil.cpu_freq()
    if freq:
        return {
            'current': freq.current,
            'min': freq.min,
            'max': freq.max
        }
    return None


def get_ram_usage():
    """Get RAM usage"""
    mem = psutil.virtual_memory()
    return {
        'used': mem.used / (1024 ** 3),
        'total': mem.total / (1024 ** 3),
        'percent': mem.percent,
        'available': mem.available / (1024 ** 3)
    }


def get_disk_usage():
    """Get disk usage for C: drive"""
    try:
        disk = psutil.disk_usage('C:')
        return {
            'used': disk.used / (1024 ** 3),
            'total': disk.total / (1024 ** 3),
            'percent': disk.percent,
            'free': disk.free / (1024 ** 3)
        }
    except:
        return None


def get_disk_io():
    """Get disk I/O stats"""
    try:
        io = psutil.disk_io_counters()
        return {
            'read_mb': io.read_bytes / (1024 ** 2),
            'write_mb': io.write_bytes / (1024 ** 2),
            'read_count': io.read_count,
            'write_count': io.write_count
        }
    except:
        return None


def get_network_usage():
    """Get network I/O stats"""
    try:
        net = psutil.net_io_counters()
        return {
            'sent_mb': net.bytes_sent / (1024 ** 2),
            'recv_mb': net.bytes_recv / (1024 ** 2),
            'sent_gb': net.bytes_sent / (1024 ** 3),
            'recv_gb': net.bytes_recv / (1024 ** 3),
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv
        }
    except:
        return None


def get_network_speed():
    """Get current network speed (approximate)"""
    try:
        # Take two samples
        net1 = psutil.net_io_counters()
        import time
        time.sleep(0.5)
        net2 = psutil.net_io_counters()

        upload_speed = (net2.bytes_sent - net1.bytes_sent) * 2 / 1024  # KB/s
        download_speed = (net2.bytes_recv - net1.bytes_recv) * 2 / 1024  # KB/s

        return {
            'upload_kbps': upload_speed,
            'download_kbps': download_speed,
            'upload_mbps': upload_speed / 1024,
            'download_mbps': download_speed / 1024
        }
    except:
        return None


def get_temperatures():
    """Get system temperatures (if available)"""
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            result = {}
            for name, entries in temps.items():
                for entry in entries:
                    result[f"{name}_{entry.label}"] = entry.current
            return result
        return None
    except:
        return None


def get_battery():
    """Get battery information (if laptop)"""
    try:
        battery = psutil.sensors_battery()
        if battery:
            return {
                'percent': battery.percent,
                'plugged': battery.power_plugged,
                'time_left': battery.secsleft if battery.secsleft != -1 else None
            }
        return None
    except:
        return None


def get_current_time(format_str="%H:%M:%S"):
    """Get current time"""
    return datetime.now().strftime(format_str)


def get_date(format_str="%Y-%m-%d"):
    """Get current date"""
    return datetime.now().strftime(format_str)


def get_uptime():
    """Get system uptime"""
    try:
        boot_time = psutil.boot_time()
        uptime_seconds = datetime.now().timestamp() - boot_time

        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)

        return {
            'seconds': uptime_seconds,
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'formatted': f"{days}d {hours}h {minutes}m"
        }
    except:
        return None


def get_system_info():
    """Get system information"""
    return {
        'os': platform.system(),
        'os_version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'hostname': platform.node()
    }


def get_all_metrics():
    """Get all available metrics"""
    ram = get_ram_usage()
    disk = get_disk_usage()
    net = get_network_usage()

    metrics = {
        'cpu_percent': get_cpu_usage(),
        'ram_used': ram['used'],
        'ram_total': ram['total'],
        'ram_percent': ram['percent'],
        'time': get_current_time()
    }

    # Add disk if available
    if disk:
        metrics['disk_used'] = disk['used']
        metrics['disk_total'] = disk['total']
        metrics['disk_percent'] = disk['percent']

    # Add network if available
    if net:
        metrics['net_sent_gb'] = net['sent_gb']
        metrics['net_recv_gb'] = net['recv_gb']

    return metrics


# For testing
if __name__ == "__main__":
    print("Extended System Metrics Test")
    print("=" * 70)

    print("\n[CPU]")
    print(f"Usage: {get_cpu_usage():.1f}%")
    freq = get_cpu_freq()
    if freq:
        print(f"Frequency: {freq['current']:.0f} MHz")

    print("\n[RAM]")
    ram = get_ram_usage()
    print(f"Usage: {ram['used']:.2f} / {ram['total']:.2f} GB ({ram['percent']:.1f}%)")

    print("\n[Disk]")
    disk = get_disk_usage()
    if disk:
        print(f"C: {disk['used']:.1f} / {disk['total']:.1f} GB ({disk['percent']:.1f}%)")

    print("\n[Network]")
    net = get_network_usage()
    if net:
        print(f"Sent: {net['sent_gb']:.2f} GB")
        print(f"Received: {net['recv_gb']:.2f} GB")

    print("\n[System]")
    uptime = get_uptime()
    if uptime:
        print(f"Uptime: {uptime['formatted']}")

    print(f"Time: {get_current_time()}")
    print(f"Date: {get_date()}")
