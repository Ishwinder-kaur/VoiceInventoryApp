from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.businesses import router as businesses_router
from app.routers.customers import router as customers_router
from app.routers.products import router as products_router
from app.routers.sales import router as sales_router
from app.routers.audit import router as audit_router
from app.routers.voice import router as voice_router
from app.routers.assistant import router as assistant_router


app = FastAPI(
    title="Voice Inventory API",
    version="0.1.0",
    description="Backend API for the Voice Inventory System.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(businesses_router)
app.include_router(customers_router)
app.include_router(products_router)
app.include_router(sales_router)
app.include_router(audit_router)
app.include_router(voice_router)
app.include_router(assistant_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}