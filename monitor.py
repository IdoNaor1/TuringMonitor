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
    Get GPU usage information from LibreHardwareMonitor

    Returns:
        dict or None: Dictionary containing GPU metrics if available:
            - gpu_percent: GPU usage percentage (0-100)
            - gpu_memory_percent: GPU memory usage percentage (0-100)
            - gpu_temp: GPU temperature in Celsius
            - gpu_hotspot_temp: GPU hot spot temperature in Celsius (if available)
            - gpu_name: GPU model name
            - gpu_clock: GPU core clock in MHz (if available)
            - gpu_memory_clock: GPU memory clock in MHz (if available)
            - gpu_power: GPU power consumption in Watts (if available)
            - gpu_memory_used: GPU memory used in MB (if available)
            - gpu_memory_total: GPU memory total in MB (if available)
        Returns None if no GPU data available
    """
    try:
        import urllib.request
        import json
        
        # Try to fetch from LibreHardwareMonitor web server
        url = "http://localhost:8085/data.json"
        with urllib.request.urlopen(url, timeout=1) as response:
            data = json.loads(response.read().decode())
            
            # Recursively search for GPU data
            def find_gpu_data(node):
                text = node.get('Text', '')
                hardware_id = node.get('HardwareId', '').lower()
                
                # Check if this is a GPU node (NVIDIA or AMD)
                if ('nvidia' in text.lower() or 'geforce' in text.lower() or 'rtx' in text.lower() or 
                    'radeon' in text.lower() or 'amd' in text.lower()) and \
                   ('gpu-nvidia' in hardware_id or 'gpu-amd' in hardware_id or 'gpu-intel' in hardware_id):
                    
                    gpu_data = {'gpu_name': text}
                    
                    # Parse all children to extract metrics
                    for child in node.get('Children', []):
                        child_text = child.get('Text', '')
                        
                        # Temperatures
                        if 'Temperature' in child_text:
                            for sensor in child.get('Children', []):
                                sensor_text = sensor.get('Text', '')
                                value_str = sensor.get('Value', '0.0')
                                
                                if 'GPU Core' in sensor_text and 'gpu_temp' not in gpu_data:
                                    gpu_data['gpu_temp'] = float(value_str.replace('°C', '').replace('°', '').strip())
                                elif 'Hot Spot' in sensor_text or 'Hotspot' in sensor_text:
                                    gpu_data['gpu_hotspot_temp'] = float(value_str.replace('°C', '').replace('°', '').strip())
                        
                        # Load/Usage
                        elif 'Load' in child_text:
                            for sensor in child.get('Children', []):
                                sensor_text = sensor.get('Text', '')
                                value_str = sensor.get('Value', '0.0 %')
                                
                                if 'GPU Core' in sensor_text and 'gpu_percent' not in gpu_data:
                                    gpu_data['gpu_percent'] = float(value_str.replace('%', '').strip())
                                elif 'GPU Memory' in sensor_text and 'gpu_memory_percent' not in gpu_data:
                                    gpu_data['gpu_memory_percent'] = float(value_str.replace('%', '').strip())
                        
                        # Clocks
                        elif 'Clock' in child_text:
                            for sensor in child.get('Children', []):
                                sensor_text = sensor.get('Text', '')
                                value_str = sensor.get('Value', '0.0 MHz')
                                
                                if 'GPU Core' in sensor_text:
                                    gpu_data['gpu_clock'] = float(value_str.replace('MHz', '').strip())
                                elif 'GPU Memory' in sensor_text:
                                    gpu_data['gpu_memory_clock'] = float(value_str.replace('MHz', '').strip())
                        
                        # Power
                        elif 'Power' in child_text:
                            for sensor in child.get('Children', []):
                                sensor_text = sensor.get('Text', '')
                                value_str = sensor.get('Value', '0.0 W')
                                
                                if 'GPU' in sensor_text or 'Package' in sensor_text:
                                    gpu_data['gpu_power'] = float(value_str.replace('W', '').strip())
                        
                        # Memory Data (MB)
                        elif 'Data' in child_text or 'SmallData' in child_text:
                            for sensor in child.get('Children', []):
                                sensor_text = sensor.get('Text', '')
                                value_str = sensor.get('Value', '0.0 MB')
                                
                                if 'Memory Used' in sensor_text:
                                    gpu_data['gpu_memory_used'] = float(value_str.replace('MB', '').replace('GB', '').strip())
                                    if 'GB' in value_str:
                                        gpu_data['gpu_memory_used'] *= 1024
                                elif 'Memory Total' in sensor_text:
                                    gpu_data['gpu_memory_total'] = float(value_str.replace('MB', '').replace('GB', '').strip())
                                    if 'GB' in value_str:
                                        gpu_data['gpu_memory_total'] *= 1024
                    
                    # Only return if we got at least temperature or load data
                    if 'gpu_temp' in gpu_data or 'gpu_percent' in gpu_data:
                        # Set defaults for missing values
                        gpu_data.setdefault('gpu_percent', 0.0)
                        gpu_data.setdefault('gpu_memory_percent', 0.0)
                        gpu_data.setdefault('gpu_temp', 0.0)
                        return gpu_data
                
                # Recursively search children
                for child in node.get('Children', []):
                    result = find_gpu_data(child)
                    if result:
                        return result
                return None
            
            return find_gpu_data(data)
    except Exception as e:
        # Silently fail - GPU monitoring is optional
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


def get_cpu_temp_from_libre_hardware_monitor():
    """
    Get CPU temperature from LibreHardwareMonitor web server
    
    Returns:
        float: CPU temperature in Celsius, or 0 if not available
    """
    try:
        import urllib.request
        import json
        
        # Try to fetch from LibreHardwareMonitor web server
        url = "http://localhost:8085/data.json"
        with urllib.request.urlopen(url, timeout=1) as response:
            data = json.loads(response.read().decode())
            
            # Recursively search for CPU temperature
            def find_cpu_temp(node):
                text = node.get('Text', '')
                
                # Check if this is a CPU node (Intel or AMD)
                if ('Intel Core' in text or 'AMD Ryzen' in text or 'AMD EPYC' in text) and 'intelcpu' in node.get('HardwareId', '').lower() or 'amdcpu' in node.get('HardwareId', '').lower():
                    # Found the CPU, now look for temperatures
                    for child in node.get('Children', []):
                        if 'Temperature' in child.get('Text', ''):
                            # Found temperatures section
                            for temp_sensor in child.get('Children', []):
                                sensor_text = temp_sensor.get('Text', '')
                                # Look for CPU Package or Core Average (prefer Package)
                                if 'CPU Package' in sensor_text or 'Package' in sensor_text:
                                    value_str = temp_sensor.get('Value', '0.0 °C')
                                    temp = float(value_str.replace('°C', '').replace('°', '').strip())
                                    return temp
                                elif 'Core Average' in sensor_text or 'Average' in sensor_text:
                                    value_str = temp_sensor.get('Value', '0.0 °C')
                                    temp = float(value_str.replace('°C', '').replace('°', '').strip())
                                    return temp
                
                # Recursively search children
                for child in node.get('Children', []):
                    result = find_cpu_temp(child)
                    if result > 0:
                        return result
                return 0
            
            return find_cpu_temp(data)
    except Exception as e:
        # Silently fail
        pass
    return 0


def get_ram_temperatures():
    """
    Get RAM/DIMM temperatures from LibreHardwareMonitor

    Returns:
        dict: Dictionary containing:
            - dimm_1_temp: DIMM #1 temperature in Celsius (0 if unavailable)
            - dimm_2_temp: DIMM #2 temperature in Celsius (0 if unavailable)
            - dimm_3_temp: DIMM #3 temperature in Celsius (0 if unavailable)
            - dimm_4_temp: DIMM #4 temperature in Celsius (0 if unavailable)
            - ram_temp_avg: Average temperature of populated DIMMs (0 if none)
    """
    try:
        import urllib.request
        import json
        
        url = "http://localhost:8085/data.json"
        with urllib.request.urlopen(url, timeout=1) as response:
            data = json.loads(response.read().decode())
            
            # Recursively search for RAM/DIMM temperature sensors
            def find_dimm_temps(node):
                temps = {}
                
                if isinstance(node, dict):
                    # Check if this is a DIMM temperature node
                    if node.get('Type') == 'Temperature' and 'DIMM' in node.get('Text', ''):
                        dimm_text = node.get('Text', '')
                        value_str = node.get('Value', '0.0 °C')
                        try:
                            temp = float(value_str.split()[0])
                            # Extract DIMM number from text like "DIMM #1", "DIMM #3"
                            if '#' in dimm_text:
                                dimm_num = dimm_text.split('#')[1].split()[0]
                                temps[f'dimm_{dimm_num}_temp'] = temp
                        except (ValueError, IndexError):
                            pass
                    
                    # Recursively search children
                    if 'Children' in node:
                        for child in node['Children']:
                            temps.update(find_dimm_temps(child))
                elif isinstance(node, list):
                    for item in node:
                        temps.update(find_dimm_temps(item))
                
                return temps
            
            dimm_temps = find_dimm_temps(data)
            
            # Ensure all 4 DIMM slots are represented (0 if not found)
            result = {
                'dimm_1_temp': dimm_temps.get('dimm_1_temp', 0),
                'dimm_2_temp': dimm_temps.get('dimm_2_temp', 0),
                'dimm_3_temp': dimm_temps.get('dimm_3_temp', 0),
                'dimm_4_temp': dimm_temps.get('dimm_4_temp', 0)
            }
            
            # Calculate average of populated DIMMs
            populated_temps = [temp for temp in result.values() if temp > 0]
            if populated_temps:
                result['ram_temp_avg'] = round(sum(populated_temps) / len(populated_temps), 1)
            else:
                result['ram_temp_avg'] = 0
            
            return result
    except Exception:
        pass
    
    return {'dimm_1_temp': 0, 'dimm_2_temp': 0, 'dimm_3_temp': 0, 'dimm_4_temp': 0, 'ram_temp_avg': 0}


def get_nvme_temperature():
    """
    Get NVMe SSD temperature from LibreHardwareMonitor

    Returns:
        float: NVMe temperature in Celsius (0 if unavailable)
    """
    try:
        import urllib.request
        import json
        
        url = "http://localhost:8085/data.json"
        with urllib.request.urlopen(url, timeout=1) as response:
            data = json.loads(response.read().decode())
            
            # Recursively search for NVMe temperature
            def find_nvme_temp(node):
                if isinstance(node, dict):
                    # Check if this is an NVMe device
                    if node.get('HardwareId', '').startswith('/nvme/'):
                        # Look for temperature in children
                        for child in node.get('Children', []):
                            if child.get('Text') == 'Temperatures':
                                # Get first temperature sensor (usually the main one)
                                for temp_sensor in child.get('Children', []):
                                    if temp_sensor.get('Type') == 'Temperature':
                                        value_str = temp_sensor.get('Value', '0.0 °C')
                                        try:
                                            return float(value_str.split()[0])
                                        except (ValueError, IndexError):
                                            pass
                    
                    # Recursively search children
                    if 'Children' in node:
                        for child in node['Children']:
                            temp = find_nvme_temp(child)
                            if temp > 0:
                                return temp
                elif isinstance(node, list):
                    for item in node:
                        temp = find_nvme_temp(item)
                        if temp > 0:
                            return temp
                
                return 0
            
            return find_nvme_temp(data)
    except Exception:
        pass
    return 0


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
    Get current network upload/download speed from LibreHardwareMonitor
    Falls back to psutil if LibreHardwareMonitor is unavailable

    Returns:
        dict: Dictionary containing:
            - upload_kbs: Upload speed in KB/s
            - download_kbs: Download speed in KB/s
            - upload_mbs: Upload speed in MB/s
            - download_mbs: Download speed in MB/s
    """
    # Try LibreHardwareMonitor first
    try:
        import urllib.request
        import json
        
        url = "http://localhost:8085/data.json"
        with urllib.request.urlopen(url, timeout=1) as response:
            data = json.loads(response.read().decode())
            
            # Find active network adapter with throughput data
            def find_network_speed(node):
                speeds = {'upload_kbs': 0.0, 'download_kbs': 0.0}
                
                if isinstance(node, dict):
                    # Check if this is a network adapter node
                    if node.get('HardwareId', '').startswith('/nic/'):
                        # Look for throughput data in children
                        for child in node.get('Children', []):
                            if child.get('Text') == 'Throughput':
                                for sensor in child.get('Children', []):
                                    text = sensor.get('Text', '')
                                    value_str = sensor.get('Value', '0.0 KB/s')
                                    try:
                                        # Parse value and unit
                                        parts = value_str.split()
                                        value = float(parts[0])
                                        unit = parts[1] if len(parts) > 1 else 'KB/s'
                                        
                                        # Convert to KB/s
                                        if 'MB/s' in unit:
                                            value = value * 1024
                                        elif 'GB/s' in unit:
                                            value = value * 1024 * 1024
                                        
                                        if 'Upload' in text:
                                            speeds['upload_kbs'] = max(speeds['upload_kbs'], value)
                                        elif 'Download' in text:
                                            speeds['download_kbs'] = max(speeds['download_kbs'], value)
                                    except (ValueError, IndexError):
                                        pass
                    
                    # Recursively search children
                    if 'Children' in node:
                        for child in node['Children']:
                            child_speeds = find_network_speed(child)
                            # Use the adapter with the highest speeds
                            if child_speeds['upload_kbs'] > speeds['upload_kbs']:
                                speeds['upload_kbs'] = child_speeds['upload_kbs']
                            if child_speeds['download_kbs'] > speeds['download_kbs']:
                                speeds['download_kbs'] = child_speeds['download_kbs']
                elif isinstance(node, list):
                    for item in node:
                        child_speeds = find_network_speed(item)
                        if child_speeds['upload_kbs'] > speeds['upload_kbs']:
                            speeds['upload_kbs'] = child_speeds['upload_kbs']
                        if child_speeds['download_kbs'] > speeds['download_kbs']:
                            speeds['download_kbs'] = child_speeds['download_kbs']
                
                return speeds
            
            speeds = find_network_speed(data)
            return {
                'upload_kbs': round(speeds['upload_kbs'], 2),
                'download_kbs': round(speeds['download_kbs'], 2),
                'upload_mbs': round(speeds['upload_kbs'] / 1024, 3),
                'download_mbs': round(speeds['download_kbs'] / 1024, 3)
            }
    except Exception:
        pass
    
    # Fallback to psutil method
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
    Calculate disk read/write speeds from LibreHardwareMonitor
    Falls back to psutil if LibreHardwareMonitor is unavailable

    Returns:
        dict: Dictionary containing:
            - disk_read_mbs: Read speed in MB/s
            - disk_write_mbs: Write speed in MB/s
            - disk_read_kbs: Read speed in KB/s
            - disk_write_kbs: Write speed in KB/s
    """
    # Try LibreHardwareMonitor first
    try:
        import urllib.request
        import json
        
        url = "http://localhost:8085/data.json"
        with urllib.request.urlopen(url, timeout=1) as response:
            data = json.loads(response.read().decode())
            
            # Find NVMe/disk throughput data
            def find_disk_speed(node):
                speeds = {'read_mbs': 0.0, 'write_mbs': 0.0}
                
                if isinstance(node, dict):
                    # Check if this is an NVMe/storage device node
                    if node.get('HardwareId', '').startswith('/nvme/'):
                        # Look for throughput data in children
                        for child in node.get('Children', []):
                            if child.get('Text') == 'Throughput':
                                for sensor in child.get('Children', []):
                                    text = sensor.get('Text', '')
                                    value_str = sensor.get('Value', '0.0 KB/s')
                                    try:
                                        # Parse value and unit
                                        parts = value_str.split()
                                        value = float(parts[0])
                                        unit = parts[1] if len(parts) > 1 else 'KB/s'
                                        
                                        # Convert to MB/s
                                        if 'KB/s' in unit:
                                            value = value / 1024
                                        elif 'GB/s' in unit:
                                            value = value * 1024
                                        # else already in MB/s
                                        
                                        if 'Read' in text:
                                            speeds['read_mbs'] = max(speeds['read_mbs'], value)
                                        elif 'Write' in text:
                                            speeds['write_mbs'] = max(speeds['write_mbs'], value)
                                    except (ValueError, IndexError):
                                        pass
                    
                    # Recursively search children
                    if 'Children' in node:
                        for child in node['Children']:
                            child_speeds = find_disk_speed(child)
                            # Use the disk with the highest speeds (active disk)
                            if child_speeds['read_mbs'] > speeds['read_mbs']:
                                speeds['read_mbs'] = child_speeds['read_mbs']
                            if child_speeds['write_mbs'] > speeds['write_mbs']:
                                speeds['write_mbs'] = child_speeds['write_mbs']
                elif isinstance(node, list):
                    for item in node:
                        child_speeds = find_disk_speed(item)
                        if child_speeds['read_mbs'] > speeds['read_mbs']:
                            speeds['read_mbs'] = child_speeds['read_mbs']
                        if child_speeds['write_mbs'] > speeds['write_mbs']:
                            speeds['write_mbs'] = child_speeds['write_mbs']
                
                return speeds
            
            speeds = find_disk_speed(data)
            return {
                'disk_read_mbs': round(speeds['read_mbs'], 2),
                'disk_write_mbs': round(speeds['write_mbs'], 2),
                'disk_read_kbs': round(speeds['read_mbs'] * 1024, 1),
                'disk_write_kbs': round(speeds['write_mbs'] * 1024, 1)
            }
    except Exception:
        pass
    
    # Fallback to psutil method
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
    ram_temps = get_ram_temperatures()
    nvme_temp = get_nvme_temperature()

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

    # Add RAM temperatures
    metrics.update(ram_temps)
    
    # Add NVMe temperature
    metrics['nvme_temp'] = nvme_temp

    # Add GPU metrics if available
    if gpu:
        metrics.update({
            'gpu_percent': gpu['gpu_percent'],
            'gpu_memory_percent': gpu['gpu_memory_percent'],
            'gpu_temp': gpu['gpu_temp'],
            'gpu_name': gpu['gpu_name']
        })
        # Add optional GPU metrics if available
        if 'gpu_hotspot_temp' in gpu:
            metrics['gpu_hotspot_temp'] = gpu['gpu_hotspot_temp']
        if 'gpu_clock' in gpu:
            metrics['gpu_clock'] = gpu['gpu_clock']
        if 'gpu_memory_clock' in gpu:
            metrics['gpu_memory_clock'] = gpu['gpu_memory_clock']
        if 'gpu_power' in gpu:
            metrics['gpu_power'] = gpu['gpu_power']
        if 'gpu_memory_used' in gpu:
            metrics['gpu_memory_used'] = gpu['gpu_memory_used']
        if 'gpu_memory_total' in gpu:
            metrics['gpu_memory_total'] = gpu['gpu_memory_total']
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
    
    # Try LibreHardwareMonitor web server first (most reliable on Windows)
    cpu_temp = get_cpu_temp_from_libre_hardware_monitor()
    
    # If that didn't work, try psutil sensors (Linux/Mac)
    if cpu_temp == 0:
        for key, value in temps.items():
            # Look for CPU temperature sensors (varies by platform)
            if any(keyword in key.lower() for keyword in ['coretemp', 'cpu', 'k10temp', 'zenpower']):
                cpu_temp = value
                break
    
    # Last resort: try WMI methods (rarely work)
    if cpu_temp == 0:
        try:
            import wmi
            # Try OpenHardwareMonitor namespace
            try:
                w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                temperature_infos = w.Sensor()
                for sensor in temperature_infos:
                    if sensor.SensorType == 'Temperature' and 'CPU' in sensor.Name:
                        cpu_temp = float(sensor.Value)
                        break
            except:
                pass
            
            # Try LibreHardwareMonitor namespace
            if cpu_temp == 0:
                try:
                    w = wmi.WMI(namespace="root\\LibreHardwareMonitor")
                    temperature_infos = w.Sensor()
                    for sensor in temperature_infos:
                        if sensor.SensorType == 'Temperature' and 'CPU' in sensor.Name:
                            cpu_temp = float(sensor.Value)
                            break
                except:
                    pass
        except:
            pass
    
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
    if 'gpu_hotspot_temp' in metrics and metrics['gpu_hotspot_temp'] > 0:
        _data_history.add_data_point('gpu_hotspot_temp', metrics['gpu_hotspot_temp'])
    
    # RAM temperatures
    if metrics.get('dimm_1_temp', 0) > 0:
        _data_history.add_data_point('dimm_1_temp', metrics['dimm_1_temp'])
    if metrics.get('dimm_2_temp', 0) > 0:
        _data_history.add_data_point('dimm_2_temp', metrics['dimm_2_temp'])
    if metrics.get('dimm_3_temp', 0) > 0:
        _data_history.add_data_point('dimm_3_temp', metrics['dimm_3_temp'])
    if metrics.get('dimm_4_temp', 0) > 0:
        _data_history.add_data_point('dimm_4_temp', metrics['dimm_4_temp'])
    if metrics.get('ram_temp_avg', 0) > 0:
        _data_history.add_data_point('ram_temp_avg', metrics['ram_temp_avg'])
    
    # NVMe temperature
    if metrics.get('nvme_temp', 0) > 0:
        _data_history.add_data_point('nvme_temp', metrics['nvme_temp'])
    
    # GPU clocks and power
    if 'gpu_clock' in metrics and metrics['gpu_clock'] > 0:
        _data_history.add_data_point('gpu_clock', metrics['gpu_clock'])
    if 'gpu_memory_clock' in metrics and metrics['gpu_memory_clock'] > 0:
        _data_history.add_data_point('gpu_memory_clock', metrics['gpu_memory_clock'])
    if 'gpu_power' in metrics and metrics['gpu_power'] > 0:
        _data_history.add_data_point('gpu_power', metrics['gpu_power'])
    if 'gpu_memory_used' in metrics and metrics['gpu_memory_used'] > 0:
        _data_history.add_data_point('gpu_memory_used', metrics['gpu_memory_used'])
    
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
    if 'gpu_hotspot_temp' in metrics:
        print(f"GPU Hotspot Temp: {metrics['gpu_hotspot_temp']:.0f}°C")
    if 'gpu_clock' in metrics:
        print(f"GPU Core Clock: {metrics['gpu_clock']:.0f} MHz")
    if 'gpu_memory_clock' in metrics:
        print(f"GPU Memory Clock: {metrics['gpu_memory_clock']:.0f} MHz")
    if 'gpu_power' in metrics:
        print(f"GPU Power: {metrics['gpu_power']:.1f} W")
    if 'gpu_memory_used' in metrics and 'gpu_memory_total' in metrics:
        print(f"GPU Memory: {metrics['gpu_memory_used']:.0f} MB / {metrics['gpu_memory_total']:.0f} MB")
    print()
    print(f"Network Upload: {metrics['net_upload_kbs']:.2f} KB/s ({metrics['net_upload_mbs']:.3f} MB/s)")
    print(f"Network Download: {metrics['net_download_kbs']:.2f} KB/s ({metrics['net_download_mbs']:.3f} MB/s)")
    print()
    print("RAM Temperatures:")
    if metrics.get('ram_temp_avg', 0) > 0:
        print(f"  Average: {metrics['ram_temp_avg']:.1f}°C")
    if metrics.get('dimm_1_temp', 0) > 0:
        print(f"  DIMM #1: {metrics['dimm_1_temp']:.1f}°C")
    if metrics.get('dimm_2_temp', 0) > 0:
        print(f"  DIMM #2: {metrics['dimm_2_temp']:.1f}°C")
    if metrics.get('dimm_3_temp', 0) > 0:
        print(f"  DIMM #3: {metrics['dimm_3_temp']:.1f}°C")
    if metrics.get('dimm_4_temp', 0) > 0:
        print(f"  DIMM #4: {metrics['dimm_4_temp']:.1f}°C")
    print()
    if metrics.get('nvme_temp', 0) > 0:
        print(f"NVMe Temperature: {metrics['nvme_temp']:.1f}°C")
