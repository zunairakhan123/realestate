from fastapi import FastAPI
from app.customers.router import router as customers_router
from app.properties.router import router as properties_router
from app.leads.router import router as leads_router

app = FastAPI(title="Realty Service API")

app.include_router(customers_router)
app.include_router(properties_router)
app.include_router(leads_router)