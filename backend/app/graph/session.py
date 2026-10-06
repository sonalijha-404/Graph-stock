from contextlib import contextmanager
from typing import Any, Generator

from neo4j import GraphDatabase, Driver, Session

from app.core.config import settings

_driver: Driver | None = None


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def verify_connectivity() -> bool:
    try:
        driver = get_driver()
        driver.verify_connectivity()
        with driver.session(database=settings.neo4j_database) as session:
            result = session.run("RETURN 1 AS result")
            record = result.single()
            return record is not None and record["result"] == 1
    except Exception:
        return False


@contextmanager
def read_session() -> Generator[Session, None, None]:
    driver = get_driver()
    session = driver.session(database=settings.neo4j_database)
    try:
        yield session
    finally:
        session.close()


def run_read(cypher: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    params = parameters or {}
    with read_session() as session:
        result = session.run(cypher, params, timeout=settings.cypher_timeout_seconds)
        return [dict(record) for record in result]
