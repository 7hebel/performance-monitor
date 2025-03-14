def get_dumps_range_for_cluster(cluster_number: int) -> range:
    start = cluster_number * 60
    end = (cluster_number + 1) * 60
    return range(start, end)

a=get_dumps_range_for_cluster(483875)
