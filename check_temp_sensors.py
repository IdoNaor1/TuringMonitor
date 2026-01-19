#!/usr/bin/env python3
"""
Diagnostic script to check available temperature sensors
Run this to see what monitoring methods work on your system
"""

import sys

print("=" * 70)
print("TEMPERATURE SENSOR DIAGNOSTIC")
print("=" * 70)

# Method 1: Check psutil sensors
print("\n[1] Checking psutil.sensors_temperatures()...")
try:
    import psutil
    temps = psutil.sensors_temperatures()
    if temps:
        print("✓ Found sensors via psutil:")
        for name, entries in temps.items():
            for entry in entries:
                label = entry.label or name
                print(f"  - {name}/{label}: {entry.current}°C")
    else:
        print("✗ No sensors found (not available on Windows)")
except AttributeError:
    print("✗ sensors_temperatures() not supported on this platform")
except Exception as e:
    print(f"✗ Error: {e}")

# Method 2: Check OpenHardwareMonitor
print("\n[2] Checking OpenHardwareMonitor WMI namespace...")
try:
    import wmi
    w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
    sensors = w.Sensor()
    temp_sensors = [s for s in sensors if s.SensorType == 'Temperature']
    
    if temp_sensors:
        print("✓ OpenHardwareMonitor is running! Found sensors:")
        for sensor in temp_sensors:
            print(f"  - {sensor.Name}: {sensor.Value}°C")
    else:
        print("✗ No temperature sensors found")
except Exception as e:
    print(f"✗ OpenHardwareMonitor not available: {e}")

# Method 3: Check LibreHardwareMonitor
print("\n[3] Checking LibreHardwareMonitor WMI namespace...")
try:
    import wmi
    # Try different namespace variations
    namespaces_to_try = [
        "root\\LibreHardwareMonitor",
        "root\\librehardwaremonitor",
        "ROOT\\LibreHardwareMonitor",
    ]
    
    found = False
    for ns in namespaces_to_try:
        try:
            w = wmi.WMI(namespace=ns)
            sensors = w.Sensor()
            temp_sensors = [s for s in sensors if s.SensorType == 'Temperature']
            
            if temp_sensors:
                print(f"✓ LibreHardwareMonitor found on namespace: {ns}")
                print("  Temperature sensors:")
                for sensor in temp_sensors:
                    print(f"    - {sensor.Name}: {sensor.Value}°C (Identifier: {sensor.Identifier})")
                found = True
                break
        except:
            continue
    
    if not found:
        print("✗ LibreHardwareMonitor not accessible via WMI")
        print("  Note: LibreHardwareMonitor must be running as Administrator!")
except ImportError:
    print("✗ WMI module not installed (run: pip install wmi)")
except Exception as e:
    print(f"✗ Error: {e}")

# Method 4: Check Win32_TemperatureProbe
print("\n[4] Checking Win32_TemperatureProbe...")
try:
    import wmi
    w = wmi.WMI(namespace="root\\cimv2")
    probes = w.Win32_TemperatureProbe()
    
    probe_list = list(probes)
    if probe_list:
        print(f"✓ Found {len(probe_list)} temperature probe(s):")
        for i, probe in enumerate(probe_list):
            print(f"\n  Probe #{i+1}:")
            print(f"    Description: {probe.Description}")
            print(f"    Status: {probe.Status}")
            print(f"    CurrentReading: {probe.CurrentReading}")
            if probe.CurrentReading:
                temp_c = (probe.CurrentReading / 10.0) - 273.15
                print(f"    → Temperature: {temp_c:.1f}°C")
            else:
                print(f"    → No temperature data available")
    else:
        print("✗ No temperature probes found (common on modern systems)")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Method 5: List all available WMI namespaces
print("\n[5] Scanning for ALL WMI namespaces...")
try:
    import wmi
    w = wmi.WMI(namespace="root")
    namespaces = [ns.Name for ns in w.__NAMESPACE()]
    
    print(f"  Found {len(namespaces)} namespaces in root:")
    for ns in sorted(namespaces):
        print(f"    - root\\{ns}")
    
    monitoring_related = [ns for ns in namespaces if any(keyword in ns.lower() 
                         for keyword in ['hardware', 'monitor', 'sensor', 'openhardware', 'libre', 'hwmonitor'])]
    
    if monitoring_related:
        print("\n  Potentially monitoring-related namespaces:")
        for ns in monitoring_related:
            print(f"    ⚠ root\\{ns}")
except Exception as e:
    print(f"✗ Error listing namespaces: {e}")

print("=" * 70)

print("""
1. LibreHardwareMonitor MUST run as Administrator for WMI access
   - Right-click LibreHardwareMonitor.exe → Run as administrator
   
2. After starting it as admin, wait 5-10 seconds for WMI to initialize

3. Keep LibreHardwareMonitor running in the background while using your app

4. If still not detected, check the namespaces listed above and let me know

After running one of these tools, run this script again to verify it works!
""")

print("=" * 70)
