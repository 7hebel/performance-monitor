import wmi
import time

def get_realtime_cpu_speed():
    # Initialize WMI interface
    c = wmi.WMI()
    while True:
        # Query the current CPU speed in MHz
        for processor in c.Win32_Processor():
            current_speed_ghz = processor.CurrentClockSpeed / 1000.0  # Convert MHz to GHz
            print(f"Current CPU Speed: {current_speed_ghz:.2f} GHz")
        time.sleep(1)  # Update every second

get_realtime_cpu_speed()
