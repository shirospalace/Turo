"""Dropshipping dashboard — single-process FastAPI app.

Run with: python app.py
Serves the JSON API under /api/* and the static single-page frontend at /.
"""
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from db import init_db
from seed import seed
from routers import products, settings, comps, listings, orders, integrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed()
    yield


app = FastAPI(title="Dropshipping Dashboard", lifespan=lifespan)

app.include_router(products.router)
app.include_router(settings.router)
app.include_router(comps.router)
app.include_router(listings.router)
app.include_router(orders.router)
app.include_router(integrations.router)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
