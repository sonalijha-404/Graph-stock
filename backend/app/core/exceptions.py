from fastapi import HTTPException


class AppHTTPException(HTTPException):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail={"error": {"code": code, "message": message}})


def graph_unavailable() -> AppHTTPException:
    return AppHTTPException(
        503,
        "GRAPH_UNAVAILABLE",
        "Graph database unavailable. Check the database connection.",
    )


def not_found(message: str = "Resource not found.") -> AppHTTPException:
    return AppHTTPException(404, "NOT_FOUND", message)


def unsupported(message: str = "This question is outside the information currently available in the portfolio graph.") -> AppHTTPException:
    return AppHTTPException(422, "UNSUPPORTED", message)


def no_results(message: str = "No matching portfolio relationships were found.") -> AppHTTPException:
    return AppHTTPException(404, "NO_RESULTS", message)


def validation_failed(message: str) -> AppHTTPException:
    return AppHTTPException(422, "VALIDATION_FAILED", message)
