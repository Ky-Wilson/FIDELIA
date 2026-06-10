import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mcp_server import router as mcp_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fidelia")

app = FastAPI(
    title="FIDELIA MCP Server",
    description="AI-native eGovernment platform for Côte d'Ivoire",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    # CORSMiddleware ne supporte pas les wildcards dans allow_origins
    # ("https://*.vercel.app" ne matchait jamais) -> on utilise une regex
    # pour autoriser tous les sous-domaines/preview deployments Vercel.
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1fms)",
        request.method, request.url.path, response.status_code, duration_ms,
    )
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Erreur non gérée sur %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Erreur interne du serveur", "detail": str(exc)},
    )


app.include_router(mcp_router, prefix="/mcp")

@app.get("/")
def root():
    return {
        "name": "FIDELIA MCP Server",
        "version": "1.0.0",
        "status": "running",
        "tools": ["convert_currency", "calculate_vat", "get_tax_deadlines", "calculate_cnps", "search_tax_code"]
    }

@app.get("/health")
def health():
    return {"status": "ok"}