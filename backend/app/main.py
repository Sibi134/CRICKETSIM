from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import teams, tournaments, matches, simulation

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cricket Simulator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(tournaments.router, prefix="/api/tournaments", tags=["tournaments"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(simulation.router, prefix="/api/matches", tags=["simulation"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Cricket Simulator API"}
