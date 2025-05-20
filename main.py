from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from pydantic import BaseModel

# Database setup
DATABASE_URL = "sqlite:///./cricket.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# SQLAlchemy Models
class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    season = Column(String)
    city = Column(String)
    date = Column(String)
    match_type = Column(String)
    player_of_match = Column(String)
    venue = Column(String)
    team1 = Column(String)
    team2 = Column(String)
    toss_winner = Column(String)
    toss_decision = Column(String)
    winner = Column(String)
    result = Column(String)
    result_margin = Column(Integer)
    target_runs = Column(Integer)
    target_overs = Column(Integer)
    super_over = Column(Boolean)
    method = Column(String)
    umpire1 = Column(String)
    umpire2 = Column(String)

    deliveries = relationship("Delivery", back_populates="match")

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    inning = Column(Integer)
    batting_team = Column(String)
    bowling_team = Column(String)
    over = Column(Integer)
    ball = Column(Integer)
    batter = Column(String)
    bowler = Column(String)
    non_striker = Column(String)
    batsman_runs = Column(Integer)
    extra_runs = Column(Integer)
    total_runs = Column(Integer)
    extras_type = Column(String)
    is_wicket = Column(Boolean)
    player_dismissed = Column(String)
    dismissal_kind = Column(String)
    fielder = Column(String)

    match = relationship("Match", back_populates="deliveries")

# Pydantic Schemas
class MatchSchema(BaseModel):
    id: int
    season: str
    city: str
    date: str
    match_type: str
    player_of_match: str
    venue: str
    team1: str
    team2: str
    toss_winner: str
    toss_decision: str
    winner: str
    result: str
    result_margin: int
    target_runs: int
    target_overs: int
    super_over: bool
    method: str
    umpire1: str
    umpire2: str

    class Config:
        orm_mode = True

class DeliverySchema(BaseModel):
    match_id: int
    inning: int
    batting_team: str
    bowling_team: str
    over: int
    ball: int
    batter: str
    bowler: str
    non_striker: str
    batsman_runs: int
    extra_runs: int
    total_runs: int
    extras_type: str
    is_wicket: bool
    player_dismissed: str
    dismissal_kind: str
    fielder: str

    class Config:
        orm_mode = True

# FastAPI app initialization
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Routes

@app.get("/")
def read_root():
    return {"message": "Welcome to the Cricket Match API"}

@app.get("/matches", response_model=list[MatchSchema])
def get_matches(db: Session = Depends(get_db)):
    return db.query(Match).limit(10).all()

@app.post("/matches", response_model=MatchSchema)
def create_match(match: MatchSchema, db: Session = Depends(get_db)):
    db_match = Match(**match.dict())
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match

@app.get("/deliveries", response_model=list[DeliverySchema])
def get_deliveries(db: Session = Depends(get_db)):
    return db.query(Delivery).limit(10).all()

@app.post("/deliveries", response_model=DeliverySchema)
def create_delivery(delivery: DeliverySchema, db: Session = Depends(get_db)):
    db_delivery = Delivery(**delivery.dict())
    db.add(db_delivery)
    db.commit()
    db.refresh(db_delivery)
    return db_delivery
