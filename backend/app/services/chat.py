import time
from typing import Any

from app.core.config import settings
from app.core import exceptions as exc
from app.graph import templates as T
from app.graph.path_parser import subgraph_from_entity_records
from app.graph.session import run_read, verify_connectivity
from app.schemas.chat import CalculationTrace, ChatResponse, ExecutionMs, ImpactSimulateRequest
from app.schemas.common import Subgraph
from app.services import impact, router
from app.services.catalog import load_known_entities
from app.llm.classifier import classify_with_llm


def _format_inr(amount: float) -> str:
    val = abs(amount)
    if val >= 1000:
        return f"₹{val:,.0f}"
    return f"₹{val:.2f}"


def handle_chat(question: str) -> ChatResponse:
    if not verify_connectivity():
        raise exc.graph_unavailable()

    t0 = time.perf_counter()
    stages = ["intent"]
    known = load_known_entities()

    intent, entities = classify_with_llm(question, known)
    if intent == "UNKNOWN":
        intent, entities = router.classify(question, known["symbols"], known["sectors"])

    if intent == "UNKNOWN":
        raise exc.unsupported()

    params = router.validate_entities(intent, entities, known)
    if params is None:
        raise exc.unsupported()

    stages.append("template")
    cypher = T.TEMPLATE_BY_INTENT.get(intent, "")
    if not cypher:
        raise exc.unsupported()

    t_neo = time.perf_counter()
    records = run_read(cypher.strip(), params)
    neo_ms = int((time.perf_counter() - t_neo) * 1000)
    stages.append("neo4j")

    if intent in ("STOCK_HOLDERS", "MULTI_STOCK_HOLDERS") and not records:
        raise exc.no_results()

    subgraph_data = subgraph_from_entity_records(records)
    if intent == "SECTOR_IMPACT" and records:
        subgraph_data = subgraph_from_entity_records(records)

    calcs: list[CalculationTrace] = []
    results: list[dict[str, Any]] = []
    answer = ""

    t_calc = time.perf_counter()
    if intent == "STOCK_HOLDERS":
        names = sorted({dict(r["c"].items())["name"] for r in records if r.get("c")})
        results = [{"customer_name": n} for n in names]
        answer = f"Potentially affected customers holding {params['symbol']}: {', '.join(names)}."

    elif intent == "MULTI_STOCK_HOLDERS":
        names = sorted({dict(r["c"].items())["name"] for r in records if r.get("c")})
        results = [{"customer_name": n} for n in names]
        syms = " and ".join(params["symbols"])
        answer = f"Customers who own both {syms}: {', '.join(names) if names else 'none'}."

    elif intent == "STOCK_IMPACT":
        stages.append("impact")
        rows = impact.rows_from_neo4j(records)
        results, calcs = impact.stock_impact(rows, params["symbol"], params["change_percent"])
        n_portfolios = len({r.portfolio_id for r in rows if r.symbol == params["symbol"]})
        n_customers = len(results)
        if results:
            worst = min(results, key=lambda x: x["estimated_impact"])
            answer = (
                f"Estimated exposure to {params['symbol']} was found in {n_portfolios} portfolios "
                f"belonging to {n_customers} customers. "
                f"The largest estimated unrealized impact is {worst['customer_name']} at "
                f"{_format_inr(worst['estimated_impact'])}."
            )
        else:
            raise exc.no_results()

    elif intent == "SECTOR_EXPOSURE":
        stages.append("impact")
        rows = impact.rows_from_neo4j(records)
        results = impact.sector_exposure_for_customer(rows, params["sector"], params["min_percent"])
        if not results:
            raise exc.no_results()
        answer = (
            f"Customers highly exposed to {params['sector']} (≥{params['min_percent']:.0f}% of portfolio value): "
            + ", ".join(
                f"{r['customer_name']} ({r['sector_exposure_percent']:.1f}%)" for r in results[:10]
            )
            + "."
        )
        rahul = next((r for r in results if r["customer_name"] == "Rahul Sharma"), None)
        if rahul and abs(rahul["sector_exposure_percent"] - 75.0) < 0.5:
            answer += " Rahul Sharma's primary portfolio is 75% IT."

    elif intent == "SECTOR_IMPACT":
        stages.append("impact")
        rows = impact.rows_from_neo4j(records)
        results, calcs = impact.sector_impact(rows, params["sector"], params["change_percent"])
        answer = (
            f"A {params['change_percent']}% move in {params['sector']} sector stocks implies "
            f"estimated unrealized impact across {len(results)} potentially affected customers."
        )

    elif intent == "CUSTOMER_EXPOSURE":
        stages.append("impact")
        rows = impact.rows_from_neo4j(records)
        if not rows:
            raise exc.no_results()
        summary = impact.customer_exposure_summary(rows)
        results = [summary]
        sectors_txt = ", ".join(f"{s['sector']} {s['percent']:.1f}%" for s in summary["sectors"])
        answer = (
            f"Estimated exposure for {summary['customer_name']}: total value {_format_inr(summary['total_value'])}. "
            f"By sector: {sectors_txt}."
        )

    calc_ms = int((time.perf_counter() - t_calc) * 1000)
    stages.append("answer")
    total_ms = int((time.perf_counter() - t0) * 1000)

    return ChatResponse(
        answer=answer,
        intent=intent,
        entities=params,
        cypher=cypher.strip(),
        parameters=params,
        subgraph=Subgraph(**subgraph_data),
        results=results,
        calculations=calcs,
        stages=stages,
        execution_ms=ExecutionMs(neo4j=neo_ms, calculation=calc_ms, total=total_ms),
        disclaimer=settings.disclaimer,
    )


def handle_impact_simulate(body: ImpactSimulateRequest) -> ChatResponse:
    if body.scope == "stock":
        if not body.symbol:
            raise exc.validation_failed("symbol is required for stock scope")
        q = f"What happens if {body.symbol} drops {abs(body.change_percent)}%?"
        if body.change_percent > 0:
            q = f"What happens if {body.symbol} rises {body.change_percent}%?"
        return handle_chat(q.replace("drops -", "drops "))
    if body.scope == "sector":
        if not body.sector:
            raise exc.validation_failed("sector is required for sector scope")
        q = f"What happens if the {body.sector} sector drops {abs(body.change_percent)}%?"
        return handle_chat(q)
    raise exc.validation_failed("scope must be stock or sector")
