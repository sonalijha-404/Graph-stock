from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.graph.session import verify_connectivity

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    db_ok = verify_connectivity()
    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={"status": "ok" if db_ok else "degraded", "neo4j": "up" if db_ok else "down"},
    )
