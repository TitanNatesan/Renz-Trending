from fastapi import FastAPI
from app.database import engine, Base

app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)