from fastapi import FastAPI

from app.api.checks import router as checks_router

app = FastAPI(
    title="Credit Docs Checker",
    description="Сервис проверки пакетов документов по льготным кредитным программам",
    version="1.0.0",
)

app.include_router(checks_router)


@app.get("/health", tags=["service"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
