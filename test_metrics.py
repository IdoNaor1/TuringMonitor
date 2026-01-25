#!/usr/bin/env python3
"""Detailed timing test for get_all_metrics components"""
import time

print("=" * 60)
print("DETAILED get_all_metrics() TIMING")
print("=" * 60)

# Import after print to see any import slowness
print("\nImporting monitor module...")
import_start = time.time()
import monitor
print(f"Import took: {(time.time()-import_start)*1000:.0f}ms")

print("\n--- Individual function timings ---\n")

# Test each function called by get_all_metrics

funcs_to_test = [
    ('get_ram_usage', monitor.get_ram_usage),
    ('get_disk_usage', monitor.get_disk_usage),
    ('get_gpu_usage', monitor.get_gpu_usage),
    ('get_network_speed', monitor.get_network_speed),
    ('get_component_temperatures', monitor.get_component_temperatures),
    ('get_cpu_frequency', monitor.get_cpu_frequency),
    ('get_per_core_cpu', monitor.get_per_core_cpu),
    ('get_disk_io_speed', monitor.get_disk_io_speed),
    ('get_ram_temperatures', monitor.get_ram_temperatures),
    ('get_nvme_temperature', monitor.get_nvme_temperature),
    ('get_cpu_usage', monitor.get_cpu_usage),
    ('get_cpu_temp_from_libre_hardware_monitor', monitor.get_cpu_temp_from_libre_hardware_monitor),
]

for name, func in funcs_to_test:
    start = time.time()
    try:
        result = func()
        elapsed = (time.time() - start) * 1000
        status = "OK"
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        status = f"ERROR: {e}"
    
    if elapsed > 100:
        flag = " <<<< SLOW!"
    else:
        flag = ""
    print(f"{name:45} {elapsed:8.0f}ms  {status}{flag}")

# Now test the full function
print("\n--- Full get_all_metrics() ---\n")
start = time.time()
data = monitor.get_all_metrics()
print(f"get_all_metrics(): {(time.time()-start)*1000:.0f}ms")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
