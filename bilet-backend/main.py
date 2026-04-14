from fastapi import FastAPI
from routers import auth, events
from database import engine
from fastapi.middleware.cors import CORSMiddleware
import models

app = FastAPI(title= "BiletSistemi API")

# origins = [
#     "http://localhost:5173",
#     "http://127.0.0.1:5173"
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

app.include_router(events.router)
app.include_router(auth.router)

app.get("/")
def root():
    return {"status": "OK"}