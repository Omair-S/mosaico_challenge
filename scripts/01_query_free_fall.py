from mosaicolabs import MosaicoClient

from config import HOST, PORT, CLUSTER_GAP_NS
from freefall import free_fall_query

with MosaicoClient.connect(HOST, PORT) as client:
    qresponse = client.query(query=free_fall_query())

    if not qresponse:
        print("No matches, try widening the z band")
    else:
        for item in qresponse:
            print(f"Sequence: {item.sequence.name}")
            for topic in item.topics:
                print(f"  Topic: {topic.name}")
                # Split matches into separate windows (gaps > 100 ms start a new one)
                for i, cluster in enumerate(topic.clusterize(clustering_dt_ns=CLUSTER_GAP_NS)):
                    print(f"  Window {i}: {cluster}")
                    print(f"    Timerange: {(cluster.timerange.end - cluster.timerange.start)/1e6}ms")
