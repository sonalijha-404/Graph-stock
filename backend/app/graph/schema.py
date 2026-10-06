CONSTRAINTS = [
    """
    CREATE CONSTRAINT customer_id_unique IF NOT EXISTS
    FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT portfolio_id_unique IF NOT EXISTS
    FOR (p:Portfolio) REQUIRE p.portfolio_id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT holding_id_unique IF NOT EXISTS
    FOR (h:Holding) REQUIRE h.holding_id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT stock_symbol_unique IF NOT EXISTS
    FOR (s:Stock) REQUIRE s.symbol IS UNIQUE
    """,
    """
    CREATE CONSTRAINT sector_name_unique IF NOT EXISTS
    FOR (s:Sector) REQUIRE s.name IS UNIQUE
    """,
    """
    CREATE CONSTRAINT exchange_id_unique IF NOT EXISTS
    FOR (e:Exchange) REQUIRE e.exchange_id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT event_id_unique IF NOT EXISTS
    FOR (e:MarketEvent) REQUIRE e.event_id IS UNIQUE
    """,
]


def apply_schema() -> None:
    from app.graph.session import read_session

    with read_session() as session:
        for stmt in CONSTRAINTS:
            session.run(stmt.strip())
