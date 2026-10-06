"""Parameterized Cypher templates — never built from user text."""

STOCK_HOLDERS = """
MATCH (s:Stock {symbol: $symbol})<-[:HOLDS]-(h:Holding)<-[:HAS_HOLDING]-(p:Portfolio)<-[:OWNS]-(c:Customer)
RETURN DISTINCT c, p, h, s
LIMIT 100
"""

MULTI_STOCK_HOLDERS = """
MATCH (s:Stock)
WHERE s.symbol IN $symbols
MATCH (s)<-[:HOLDS]-(h:Holding)<-[:HAS_HOLDING]-(p:Portfolio)<-[:OWNS]-(c:Customer)
WITH c, collect(DISTINCT s.symbol) AS owned
WHERE ALL(sym IN $symbols WHERE sym IN owned)
MATCH (c)-[:OWNS]->(p2:Portfolio)-[:HAS_HOLDING]->(h2:Holding)-[:HOLDS]->(s2:Stock)
WHERE s2.symbol IN $symbols
RETURN c, p2 AS p, h2 AS h, s2 AS s
LIMIT 100
"""

STOCK_HOLDINGS_FOR_IMPACT = """
MATCH (s:Stock {symbol: $symbol})<-[:HOLDS]-(h:Holding)<-[:HAS_HOLDING]-(p:Portfolio)<-[:OWNS]-(c:Customer)
OPTIONAL MATCH (s)-[:BELONGS_TO]->(sec:Sector)
RETURN c, p, h, s, sec
LIMIT 200
"""

SECTOR_STOCKS_HOLDINGS = """
MATCH (sec:Sector {name: $sector})<-[:BELONGS_TO]-(s:Stock)<-[:HOLDS]-(h:Holding)<-[:HAS_HOLDING]-(p:Portfolio)<-[:OWNS]-(c:Customer)
RETURN sec, s, h, p, c
LIMIT 300
"""

SECTOR_EXPOSURE_FULL = """
MATCH (sec:Sector {name: $sector})<-[:BELONGS_TO]-(s:Stock)<-[:HOLDS]-(h:Holding)<-[:HAS_HOLDING]-(p:Portfolio)<-[:OWNS]-(c:Customer)
WITH DISTINCT c
MATCH (c)-[:OWNS]->(p:Portfolio)-[:HAS_HOLDING]->(h:Holding)-[:HOLDS]->(s:Stock)
OPTIONAL MATCH (s)-[:BELONGS_TO]->(sec:Sector)
RETURN c, p, h, s, sec
LIMIT 500
"""

CUSTOMER_EXPOSURE = """
MATCH (c:Customer)
WHERE ($customer_id <> '' AND c.customer_id = $customer_id) OR c.name = $customer_name
MATCH (c)-[:OWNS]->(p:Portfolio)-[:HAS_HOLDING]->(h:Holding)-[:HOLDS]->(s:Stock)
OPTIONAL MATCH (s)-[:BELONGS_TO]->(sec:Sector)
RETURN c, p, h, s, sec
LIMIT 200
"""

GRAPH_FROM_CUSTOMER = """
MATCH (c:Customer)
WHERE c.customer_id = $customer_id
MATCH path = (c)-[:OWNS|HAS_HOLDING|HOLDS|BELONGS_TO|LISTED_ON*1..$depth]-(n)
RETURN path
LIMIT 80
"""

GRAPH_FROM_STOCK = """
MATCH (s:Stock {symbol: $symbol})
MATCH path = (s)<-[:HOLDS|HAS_HOLDING|OWNS|BELONGS_TO*1..$depth]-(n)
RETURN path
LIMIT 80
"""

GRAPH_FROM_SECTOR = """
MATCH (sec:Sector {name: $sector})
MATCH path = (sec)<-[:BELONGS_TO|HOLDS|HAS_HOLDING|OWNS*1..$depth]-(n)
RETURN path
LIMIT 80
"""

STATS_COUNTS = """
MATCH (c:Customer) WITH count(c) AS customers
MATCH (p:Portfolio) WITH customers, count(p) AS portfolios
MATCH (s:Stock) WITH customers, portfolios, count(s) AS stocks
MATCH (sec:Sector) WITH customers, portfolios, stocks, count(sec) AS sectors
RETURN customers, portfolios, stocks, sectors
"""

STATS_TOTAL_VALUE = """
MATCH (h:Holding)-[:HOLDS]->(s:Stock)
RETURN sum(h.quantity * s.current_price) AS total_value
"""

STATS_TOP_SECTOR = """
MATCH (h:Holding)-[:HOLDS]->(s:Stock)-[:BELONGS_TO]->(sec:Sector)
WITH sec.name AS sector, sum(h.quantity * s.current_price) AS value
ORDER BY value DESC
LIMIT 1
RETURN sector, value
"""

STATS_TOP_CONCENTRATION = """
MATCH (p:Portfolio)-[:HAS_HOLDING]->(h:Holding)-[:HOLDS]->(s:Stock)
WITH p, sum(h.quantity * s.current_price) AS portfolio_value
MATCH (p)-[:HAS_HOLDING]->(h2:Holding)-[:HOLDS]->(s2:Stock)
WITH p, portfolio_value, s2.symbol AS symbol, sum(h2.quantity * s2.current_price) AS pos_value
WHERE portfolio_value > 0
WITH p, symbol, pos_value * 100.0 / portfolio_value AS concentration
ORDER BY concentration DESC
LIMIT 1
RETURN p.portfolio_id AS portfolio_id, p.name AS portfolio_name, symbol, concentration
"""

LATEST_EVENT = """
MATCH (e:MarketEvent)
RETURN e
ORDER BY e.timestamp DESC
LIMIT 1
"""

LIST_SYMBOLS = "MATCH (s:Stock) RETURN s.symbol AS symbol ORDER BY symbol"
LIST_SECTORS = "MATCH (s:Sector) RETURN s.name AS name ORDER BY name"
LIST_CUSTOMERS = "MATCH (c:Customer) RETURN c.customer_id AS customer_id, c.name AS name ORDER BY name"

TEMPLATE_BY_INTENT = {
    "STOCK_HOLDERS": STOCK_HOLDERS,
    "MULTI_STOCK_HOLDERS": MULTI_STOCK_HOLDERS,
    "STOCK_IMPACT": STOCK_HOLDINGS_FOR_IMPACT,
    "SECTOR_IMPACT": SECTOR_STOCKS_HOLDINGS,
    "SECTOR_EXPOSURE": SECTOR_EXPOSURE_FULL,
    "CUSTOMER_EXPOSURE": CUSTOMER_EXPOSURE,
}
