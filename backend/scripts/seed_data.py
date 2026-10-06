#!/usr/bin/env python3
"""Load synthetic portfolio graph. Safe to run twice (wipes and reloads)."""

from __future__ import annotations

import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.graph.schema import apply_schema  # noqa: E402
from app.graph.session import get_driver, read_session  # noqa: E402
from app.core.config import settings  # noqa: E402

SECTORS = [
    "IT",
    "Banking",
    "Financial Services",
    "Pharma",
    "Automobile",
    "Energy",
    "FMCG",
    "Telecommunications",
]

STOCKS = [
    ("TCS", "Tata Consultancy Services", "IT", 4000),
    ("INFY", "Infosys Limited", "IT", 2000),
    ("WIPRO", "Wipro Limited", "IT", 500),
    ("HCLTECH", "HCL Technologies", "IT", 1200),
    ("HDFCBANK", "HDFC Bank", "Banking", 2000),
    ("ICICIBANK", "ICICI Bank", "Financial Services", 1100),
    ("SBIN", "State Bank of India", "Banking", 800),
    ("SUNPHARMA", "Sun Pharmaceutical", "Pharma", 1500),
    ("RELIANCE", "Reliance Industries", "Energy", 2800),
    ("ITC", "ITC Limited", "FMCG", 450),
    ("BHARTIARTL", "Bharti Airtel", "Telecommunications", 1600),
    ("MARUTI", "Maruti Suzuki", "Automobile", 12000),
    ("TATAMOTORS", "Tata Motors", "Automobile", 900),
    ("ONGC", "Oil and Natural Gas Corp", "Energy", 250),
    ("NTPC", "NTPC Limited", "Energy", 350),
    ("KOTAKBANK", "Kotak Mahindra Bank", "Banking", 1800),
    ("AXISBANK", "Axis Bank", "Banking", 1100),
    ("BAJFINANCE", "Bajaj Finance", "Financial Services", 7000),
    ("HINDUNILVR", "Hindustan Unilever", "FMCG", 2400),
    ("NESTLEIND", "Nestle India", "FMCG", 22000),
    ("CIPLA", "Cipla Limited", "Pharma", 1400),
    ("DRREDDY", "Dr Reddy's Laboratories", "Pharma", 6000),
    ("TECHM", "Tech Mahindra", "IT", 1200),
    ("LT", "Larsen & Toubro", "Energy", 3500),
]

RISK = ["Conservative", "Moderate", "Aggressive"]
P_TYPES = ["Growth", "Income", "Balanced"]


def wipe(session):
    session.run("MATCH (n) DETACH DELETE n")


def seed(session):
    session.run(
        "CREATE (e:Exchange {exchange_id: $id, name: $name})",
        {"id": "NSE", "name": "National Stock Exchange"},
    )
    for name in SECTORS:
        session.run("CREATE (s:Sector {name: $name})", {"name": name})

    for symbol, company, sector, price in STOCKS:
        session.run(
            """
            MATCH (sec:Sector {name: $sector}), (ex:Exchange {exchange_id: 'NSE'})
            CREATE (st:Stock {symbol: $symbol, company_name: $company, current_price: $price})
            CREATE (st)-[:BELONGS_TO]->(sec)
            CREATE (st)-[:LISTED_ON]->(ex)
            """,
            {"symbol": symbol, "company": company, "sector": sector, "price": price},
        )

    # Fixture customers
    session.run(
        """
        CREATE (c:Customer {customer_id: 'C001', name: 'Rahul Sharma', risk_profile: 'Moderate', country: 'India'})
        CREATE (p:Portfolio {portfolio_id: 'P001', name: 'Rahul Growth', portfolio_type: 'Growth'})
        CREATE (c)-[:OWNS]->(p)
        """
    )
    fixture_holdings = [
        ("H001", "P001", "TCS", 100, 3800),
        ("H002", "P001", "INFY", 100, 1900),
        ("H003", "P001", "HDFCBANK", 100, 1950),
    ]
    for hid, pid, sym, qty, abp in fixture_holdings:
        session.run(
            """
            MATCH (p:Portfolio {portfolio_id: $pid}), (s:Stock {symbol: $sym})
            CREATE (h:Holding {holding_id: $hid, quantity: $qty, average_buy_price: $abp})
            CREATE (p)-[:HAS_HOLDING]->(h)-[:HOLDS]->(s)
            """,
            {"hid": hid, "pid": pid, "sym": sym, "qty": qty, "abp": abp},
        )

    session.run(
        """
        CREATE (c:Customer {customer_id: 'C002', name: 'Priya Nair', risk_profile: 'Conservative', country: 'India'})
        CREATE (p10:Portfolio {portfolio_id: 'P010', name: 'Priya Balanced', portfolio_type: 'Balanced'})
        CREATE (p11:Portfolio {portfolio_id: 'P011', name: 'Priya Pharma', portfolio_type: 'Income'})
        CREATE (c)-[:OWNS]->(p10)
        CREATE (c)-[:OWNS]->(p11)
        """
    )
    priya_holdings = [
        ("H010", "P010", "TCS", 10, 3900),
        ("H011", "P010", "SBIN", 10, 750),
        ("H012", "P011", "SUNPHARMA", 10, 1400),
    ]
    for hid, pid, sym, qty, abp in priya_holdings:
        session.run(
            """
            MATCH (p:Portfolio {portfolio_id: $pid}), (s:Stock {symbol: $sym})
            CREATE (h:Holding {holding_id: $hid, quantity: $qty, average_buy_price: $abp})
            CREATE (p)-[:HAS_HOLDING]->(h)-[:HOLDS]->(s)
            """,
            {"hid": hid, "pid": pid, "sym": sym, "qty": qty, "abp": abp},
        )

    rng = random.Random(42)
    by_sector: dict[str, list[tuple[str, int]]] = {}
    for symbol, _company, sector, price in STOCKS:
        by_sector.setdefault(sector, []).append((symbol, price))

    people = [
        ("Aarav", "Mehta"), ("Vihaan", "Kapoor"), ("Ananya", "Iyer"), ("Isha", "Banerjee"),
        ("Kabir", "Malhotra"), ("Meera", "Nambiar"), ("Rohan", "Desai"), ("Sneha", "Kulkarni"),
        ("Dev", "Chatterjee"), ("Kavya", "Pillai"), ("Arjun", "Reddy"), ("Diya", "Shah"),
        ("Ishaan", "Bose"), ("Myra", "Gill"), ("Reyansh", "Joshi"), ("Aanya", "Menon"),
        ("Vivaan", "Rao"), ("Anika", "Dutta"), ("Aditya", "Khanna"), ("Sara", "Qureshi"),
        ("Krishna", "Patil"), ("Navya", "Hegde"), ("Ayaan", "Chopra"), ("Kiara", "Sethi"),
        ("Shaurya", "Bhatt"), ("Pari", "Agarwal"), ("Atharv", "Naidu"), ("Anvi", "Kaur"),
        ("Rudra", "Saxena"), ("Zara", "Fernandes"), ("Neil", "D'Souza"), ("Inaaya", "Shetty"),
        ("Yash", "Trivedi"), ("Mira", "Chawla"), ("Om", "Bansal"), ("Tara", "Krishnan"),
        ("Laksh", "Gowda"), ("Aisha", "Ansari"), ("Veer", "Malik"), ("Nisha", "Pandey"),
        ("Harsh", "Kamat"), ("Rhea", "Lobo"), ("Manav", "Srinivasan"), ("Ira", "Mukherjee"),
        ("Jay", "Thakur"), ("Sana", "Verghese"), ("Raghav", "Unnikrishnan"), ("Leela", "Bhatt"),
    ]

    portfolio_num = 12
    holding_num = 20
    # 48 new customers. The first 24 get two portfolios so the book reaches 75
    # including Rahul's and Priya's three fixture portfolios.
    for index, (first, last) in enumerate(people):
        cid = f"C{index + 3:03d}"
        session.run(
            """
            CREATE (c:Customer {
              customer_id: $cid, name: $name,
              risk_profile: $risk, country: 'India'
            })
            """,
            {"cid": cid, "name": f"{first} {last}", "risk": RISK[index % len(RISK)]},
        )
        portfolio_count = 2 if index < 24 else 1
        for slot in range(portfolio_count):
            pid = f"P{portfolio_num:03d}"
            portfolio_num += 1
            theme = SECTORS[(index + slot * 3) % len(SECTORS)]
            ptype = P_TYPES[(index + slot) % len(P_TYPES)]
            session.run(
                """
                MATCH (c:Customer {customer_id: $cid})
                CREATE (p:Portfolio {portfolio_id: $pid, name: $pname, portfolio_type: $ptype})
                CREATE (c)-[:OWNS]->(p)
                """,
                {"cid": cid, "pid": pid, "pname": f"{first} {theme} {ptype}", "ptype": ptype},
            )
            theme_stocks = list(by_sector[theme])
            rng.shuffle(theme_stocks)
            chosen = theme_stocks[: min(3, len(theme_stocks))]
            # One holding from a different sector so books are not single-sector clones.
            other_sectors = [name for name in SECTORS if name != theme]
            other = rng.choice(by_sector[rng.choice(other_sectors)])
            if other[0] not in {sym for sym, _ in chosen}:
                chosen.append(other)
            for symbol, price in chosen:
                hid = f"H{holding_num:03d}"
                holding_num += 1
                qty = rng.randint(8, 60)
                session.run(
                    """
                    MATCH (p:Portfolio {portfolio_id: $pid}), (s:Stock {symbol: $sym})
                    CREATE (h:Holding {holding_id: $hid, quantity: $qty, average_buy_price: $abp})
                    CREATE (p)-[:HAS_HOLDING]->(h)-[:HOLDS]->(s)
                    """,
                    {"hid": hid, "pid": pid, "sym": symbol, "qty": qty, "abp": round(price * 0.92)},
                )

    enforce_guarantees(session, rng, holding_num, [s[0] for s in STOCKS])


def enforce_guarantees(session, rng, holding_num: int, symbols: list[str]):
    """Force demo constraints after random fill."""

    def add_holding(hid, cid, sym, qty=30):
        nonlocal holding_num
        session.run(
            """
            MATCH (c:Customer {customer_id: $cid})-[:OWNS]->(p:Portfolio)
            WITH c, head(collect(p)) AS p
            MATCH (s:Stock {symbol: $sym})
            CREATE (h:Holding {holding_id: $hid, quantity: $qty, average_buy_price: 1000})
            CREATE (p)-[:HAS_HOLDING]->(h)-[:HOLDS]->(s)
            """,
            {"hid": hid, "cid": cid, "sym": sym, "qty": qty},
        )
        holding_num += 1

    # At least 6 customers hold TCS
    rows = session.run(
        """
        MATCH (s:Stock {symbol: 'TCS'})<-[:HOLDS]-(:Holding)<-[:HAS_HOLDING]-(:Portfolio)<-[:OWNS]-(c:Customer)
        RETURN DISTINCT c.customer_id AS id
        """
    ).data()
    tcs_holders = {r["id"] for r in rows}
    need = 6 - len(tcs_holders)
    extras = [f"C{ i:03d}" for i in range(20, 50) if f"C{i:03d}" not in tcs_holders and f"C{i:03d}" != "C002"]
    for cid in extras[: max(0, need)]:
        add_holding(f"H{holding_num:03d}", cid, "TCS")
        holding_num += 1
        tcs_holders.add(cid)

    # At least 3 customers hold both TCS and INFY (Rahul already does)
    rows = session.run(
        """
        MATCH (s:Stock)<-[:HOLDS]-(:Holding)<-[:HAS_HOLDING]-(:Portfolio)<-[:OWNS]-(c:Customer)
        WHERE s.symbol IN ['TCS', 'INFY']
        WITH c, collect(DISTINCT s.symbol) AS syms
        WHERE 'TCS' IN syms AND 'INFY' IN syms
        RETURN c.customer_id AS id
        """
    ).data()
    both = {r["id"] for r in rows}
    need = 3 - len(both)
    candidates = [f"C{i:03d}" for i in range(15, 40) if f"C{i:03d}" not in both]
    for cid in candidates[: max(0, need)]:
        if cid not in both:
            add_holding(f"H{holding_num:03d}", cid, "TCS")
            holding_num += 1
            add_holding(f"H{holding_num:03d}", cid, "INFY")
            holding_num += 1

    # At least 1 customer with no IT stock — assign C050 only non-IT if needed
    session.run(
        """
        MATCH (c:Customer {customer_id: 'C050'})
        OPTIONAL MATCH (c)-[:OWNS]->(:Portfolio)-[:HAS_HOLDING]->(:Holding)-[:HOLDS]->(s:Stock)-[:BELONGS_TO]->(sec:Sector {name: 'IT'})
        WITH c, count(s) AS it_count
        WHERE it_count > 0
        MATCH (c)-[:OWNS]->(p:Portfolio)-[:HAS_HOLDING]->(h:Holding)-[:HOLDS]->(s:Stock)-[:BELONGS_TO]->(:Sector {name: 'IT'})
        DETACH DELETE h
        """
    )
    session.run(
        """
        MERGE (c:Customer {customer_id: 'C050'})
        ON CREATE SET c.name = 'No IT Demo User', c.risk_profile = 'Conservative', c.country = 'India'
        """
    )
    session.run(
        """
        MATCH (c:Customer {customer_id: 'C050'})
        WHERE NOT (c)-[:OWNS]->()
        CREATE (p:Portfolio {portfolio_id: 'P050', name: 'Non-IT Only', portfolio_type: 'Income'})
        CREATE (c)-[:OWNS]->(p)
        WITH p
        MATCH (s:Stock {symbol: 'SBIN'})
        CREATE (h:Holding {holding_id: 'H050', quantity: 50, average_buy_price: 700})
        CREATE (p)-[:HAS_HOLDING]->(h)-[:HOLDS]->(s)
        """
    )

    # High concentration portfolio
    session.run(
        """
        MATCH (c:Customer {customer_id: 'C030'})
        MERGE (p:Portfolio {portfolio_id: 'P900'})
        ON CREATE SET p.name = 'Concentrated Demo', p.portfolio_type = 'Growth'
        MERGE (c)-[:OWNS]->(p)
        WITH p
        MATCH (s:Stock {symbol: 'RELIANCE'})
        CREATE (h:Holding {holding_id: 'H900', quantity: 200, average_buy_price: 2500})
        CREATE (p)-[:HAS_HOLDING]->(h)-[:HOLDS]->(s)
        """
    )

    ts = datetime.now(timezone.utc).isoformat()
    events = [
        ("E001", "IT sector weakness", "sector_shock", "high", -10, "IT"),
        ("E002", "Banking stress scenario", "sector_shock", "medium", -5, "Banking"),
        ("E003", "TCS earnings volatility", "stock_shock", "medium", -8, "TCS"),
        ("E004", "Pharma rally scenario", "sector_shock", "low", 5, "Pharma"),
        ("E005", "Energy supply concern", "sector_shock", "medium", -7, "Energy"),
    ]
    for eid, title, etype, sev, pct, target in events:
        session.run(
            """
            CREATE (e:MarketEvent {
              event_id: $eid, title: $title, event_type: $etype,
              severity: $sev, change_percent: $pct, timestamp: $ts
            })
            """,
            {"eid": eid, "title": title, "etype": etype, "sev": sev, "pct": pct, "ts": ts},
        )
        if target in SECTORS:
            session.run(
                """
                MATCH (e:MarketEvent {event_id: $eid}), (sec:Sector {name: $sec})
                CREATE (e)-[:AFFECTS]->(sec)
                """,
                {"eid": eid, "sec": target},
            )
        else:
            session.run(
                """
                MATCH (e:MarketEvent {event_id: $eid}), (s:Stock {symbol: $sym})
                CREATE (e)-[:AFFECTS]->(s)
                """,
                {"eid": eid, "sym": target},
            )


def main():
    apply_schema()
    with read_session() as session:
        wipe(session)
        seed(session)
    driver = get_driver()
    with driver.session(database=settings.neo4j_database) as session:
        counts = session.run(
            """
            MATCH (c:Customer) WITH count(c) AS customers
            MATCH (p:Portfolio) WITH customers, count(p) AS portfolios
            MATCH (h:Holding) WITH customers, portfolios, count(h) AS holdings
            RETURN customers, portfolios, holdings
            """
        ).single()
        print("Seed complete:", dict(counts))


if __name__ == "__main__":
    main()
