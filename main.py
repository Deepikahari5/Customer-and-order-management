
import logging

from fastapi import FastAPI

import models  # noqa: F401  (registers tables with Base)
from database import Base, engine
from exceptions import register_exception_handlers
from routers import customers, orders

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Customer & Order Management API",
    description="Day 6 assignment: manage customers and their orders.",
    version="1.0.0",
)

register_exception_handlers(app)
app.include_router(customers.router)
app.include_router(orders.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Customer & Order Management API is running", "docs": "/docs"}
