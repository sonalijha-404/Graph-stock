from app.core import exceptions as exc
from app.graph.session import verify_connectivity


def require_graph():
    if not verify_connectivity():
        raise exc.graph_unavailable()
