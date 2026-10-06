from typing import Any

from app.core.config import settings
from app.graph.subgraph import edge_id, node_id, _id_key_for_label, _node_label


def subgraph_from_paths(path_records: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    truncated = False

    def add_node(label: str, props: dict[str, Any]) -> str | None:
        nonlocal truncated
        id_key = _id_key_for_label(label)
        key = props.get(id_key)
        if key is None:
            return None
        nid = node_id(label, str(key))
        if nid not in nodes:
            if len(nodes) >= settings.graph_node_limit:
                truncated = True
                return nid
            nodes[nid] = {
                "id": nid,
                "type": label,
                "label": _node_label(label, props),
                "properties": {k: v for k, v in props.items() if v is not None},
            }
        return nid

    for rec in path_records:
        path = rec.get("path")
        if path is None:
            continue
        for node in path.nodes:
            label = list(node.labels)[0]
            add_node(label, dict(node.items()))
        for rel in path.relationships:
            sn = rel.start_node
            en = rel.end_node
            sl = list(sn.labels)[0]
            el = list(en.labels)[0]
            sid = add_node(sl, dict(sn.items()))
            tid = add_node(el, dict(en.items()))
            if sid and tid:
                eid = edge_id(rel.type, sid, tid)
                edges[eid] = {"id": eid, "type": rel.type, "source": sid, "target": tid}
        if len(nodes) >= settings.graph_node_limit:
            truncated = True
            break

    return {"nodes": list(nodes.values()), "edges": list(edges.values()), "truncated": truncated}


def subgraph_from_entity_records(
    records: list[dict[str, Any]],
    node_limit: int | None = None,
) -> dict[str, Any]:
    cap = node_limit if node_limit is not None else settings.graph_node_limit
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    truncated = False

    def ensure_node(label: str, entity) -> str | None:
        nonlocal truncated
        if entity is None:
            return None
        props = dict(entity.items())
        id_key = _id_key_for_label(label)
        key = props.get(id_key)
        if key is None:
            return None
        nid = node_id(label, str(key))
        if nid not in nodes:
            if len(nodes) >= cap:
                truncated = True
                return nid
            nodes[nid] = {
                "id": nid,
                "type": label,
                "label": _node_label(label, props),
                "properties": props,
            }
        return nid

    def link(a: str | None, b: str | None, rtype: str) -> None:
        if not a or not b:
            return
        eid = edge_id(rtype, a, b)
        edges[eid] = {"id": eid, "type": rtype, "source": a, "target": b}

    for rec in records:
        c = rec.get("c")
        p = rec.get("p")
        h = rec.get("h")
        s = rec.get("s")
        sec = rec.get("sec")
        cid = ensure_node("Customer", c) if c else None
        pid = ensure_node("Portfolio", p) if p else None
        hid = ensure_node("Holding", h) if h else None
        sid = ensure_node("Stock", s) if s else None
        secid = ensure_node("Sector", sec) if sec else None
        if cid and pid:
            link(cid, pid, "OWNS")
        if pid and hid:
            link(pid, hid, "HAS_HOLDING")
        if hid and sid:
            link(hid, sid, "HOLDS")
        if sid and secid:
            link(sid, secid, "BELONGS_TO")
        if len(nodes) >= cap:
            truncated = True

    if len(records) > 0 and len(nodes) >= cap:
        truncated = True

    return {
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "truncated": truncated,
        "view": "complete" if cap > settings.graph_node_limit else "partial",
        "node_limit": cap,
    }
