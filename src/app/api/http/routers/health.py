from litestar import get


@get("/healthcheck/", tags=["Healthcheck"], security=[])
async def healthcheck() -> dict:
    """Liveness only — deliberately does not touch the database.

    A health endpoint that fails when the DB is briefly unreachable makes an
    orchestrator restart a perfectly healthy process.
    """
    return {"status": "ok"}
