from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, input_acquisition

app = FastAPI(title="AURA API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(input_acquisition.router)


@app.get("/")
async def root():
    return {"message": "AURA API is running"}
