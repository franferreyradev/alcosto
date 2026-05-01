from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="AlCosto API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers se registran en T5-T10
# from app.routers.admin import auth, products, orders
# from app.routers.public import products, categories, orders


@app.get("/health")
async def health():
    return {"status": "ok"}
