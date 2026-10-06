from typing import Any

from app.core.config import settings


def node_id(label: str, key: str) -> str:
    prefix = {
        "Customer": "customer",
        "Portfolio": "portfolio",
        "Holding": "holding",
        "Stock": "stock",
        "Sector": "sector",
        "Exchange": "exchange",
        "MarketEvent": "event",
    }.get(label, label.lower())
    return f"{prefix}:{key}"


def edge_id(rel_type: str, source: str, target: str) -> str:
    return f"{source}-{rel_type}-{target}"


def build_subgraph_from_paths(records: list[dict[str, Any]], limit: int | None = None) -> dict[str, Any]:
    cap = limit or settings.graph_node_limit
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}

    def add_node(label: str, props: dict[str, Any], id_key: str) -> str | None:
        key = props.get(id_key)
        if key is None:
            return None
        nid = node_id(label, str(key))
        if nid not in nodes and len(nodes) < cap:
            nodes[nid] = {
                "id": nid,
                "type": label if label != "MarketEvent" else "MarketEvent",
                "label": _node_label(label, props),
                "properties": {k: v for k, v in props.items() if v is not None},
            }
        return nid

    def add_edge(rtype: str, src: str | None, tgt: str | None) -> None:
        if not src or not tgt or len(nodes) >= cap:
            return
        eid = edge_id(rtype, src, tgt)
        if eid not in edges:
            edges[eid] = {"id": eid, "type": rtype, "source": src, "target": tgt}

    for rec in records:
        if len(nodes) >= cap:
            break
        for key, val in rec.items():
            if val is None:
                continue
            if hasattr(val, "labels") and hasattr(val, "items"):
                label = list(val.labels)[0] if val.labels else "Node"
                props = dict(val.items())
                id_key = _id_key_for_label(label)
                add_node(label, props, id_key)
            elif hasattr(val, "type") and hasattr(val, "start_node") and hasattr(val, "end_node"):
                rtype = val.type
                sn = val.start_node
                en = val.end_node
                sl = list(sn.labels)[0]
                el = list(en.labels)[0]
                sid = add_node(sl, dict(sn.items()), _id_key_for_label(sl))
                tid = add_node(el, dict(en.items()), _id_key_for_label(el))
                add_edge(rtype, sid, tid)

    truncated = len(nodes) >= cap
    return {
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "truncated": truncated,
    }


def _id_key_for_label(label: str) -> str:
    return {
        "Customer": "customer_id",
        "Portfolio": "portfolio_id",
        "Holding": "holding_id",
        "Stock": "symbol",
        "Sector": "name",
        "Exchange": "exchange_id",
        "MarketEvent": "event_id",
    }[label]


def _node_label(label: str, props: dict[str, Any]) -> str:
    if label == "Customer":
        return str(props.get("name", props.get("customer_id", "Customer")))
    if label == "Portfolio":
        return str(props.get("name", props.get("portfolio_id", "Portfolio")))
    if label == "Holding":
        return str(props.get("holding_id", "Holding"))
    if label == "Stock":
        return str(props.get("symbol", "Stock"))
    if label == "Sector":
        return str(props.get("name", "Sector"))
    if label == "Exchange":
        return str(props.get("name", "Exchange"))
    if label == "MarketEvent":
        return str(props.get("title", props.get("event_id", "Event")))
    return label


def merge_subgraphs(*subgraphs: dict[str, Any]) -> dict[str, Any]:
    nodes: dict[str, dict] = {}
    edges: dict[str, dict] = {}
    truncated = False
    for sg in subgraphs:
        for n in sg.get("nodes", []):
            if len(nodes) < settings.graph_node_limit:
                nodes[n["id"]] = n
            else:
                truncated = True
        for e in sg.get("edges", []):
            if e["source"] in nodes and e["target"] in nodes:
                edges[e["id"]] = e
        truncated = truncated or sg.get("truncated", False)
    return {"nodes": list(nodes.values()), "edges": list(edges.values()), "truncated": truncated}
