# import psutil

# def get_size(b: int) -> str:
#     for unit in ("b", "Kb", "Mb", "Gb", "Tb", "Pb"):
#         if abs(b) < 1024.0:
#             return f"{b:3.1f} {unit}"
#         b /= 1024.0

# partitions = psutil.disk_partitions()
# for partition in partitions:
#     print(f"=== Device: {partition.device} ===")
#     print(partition)
#     print(f"  Mountpoint: {partition.mountpoint}")
#     print(f"  File system type: {partition.fstype}")
#     try:
#         partition_usage = psutil.disk_usage(partition.mountpoint)
#     except PermissionError:
#         # this can be catched due to the disk that
#         # isn't ready
#         continue
#     print(f"  Total Size: {get_size(partition_usage.total)}")
#     print(f"  Used: {get_size(partition_usage.used)}")
#     print(f"  Free: {get_size(partition_usage.free)}")
#     print(f"  Percentage: {partition_usage.percent}%")
