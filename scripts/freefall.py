"""The single Mosaico free-fall query, shared by all scripts."""
from mosaicolabs import Query, QuerySequence, QueryTopic, QueryOntologyCatalog, IMU

from config import ROBOT, IMU_TOPIC, FREE_FALL_AZ, CLUSTER_GAP_NS


def free_fall_query():
    return Query(
        QuerySequence().with_user_metadata("robot", eq=ROBOT),
        QueryTopic().with_name(IMU_TOPIC),
        QueryOntologyCatalog().with_expression(
            IMU.Q.acceleration.z.lt(FREE_FALL_AZ)
        ),
    )


def free_fall_windows(client):
    """Return the query response and its matches split into windows."""
    qresponse = client.query(query=free_fall_query())
    windows = []
    for item in qresponse or []:
        for topic in item.topics:
            windows.extend(topic.clusterize(clustering_dt_ns=CLUSTER_GAP_NS))
    return qresponse, windows


def free_fall_window(client):
    """Return (start_ns, end_ns) of the first free-fall window."""
    _, windows = free_fall_windows(client)
    if not windows:
        raise RuntimeError("Free-fall query returned no matches. Is spot_yb42 ingested?")
    return windows[0].timerange.start, windows[0].timerange.end
