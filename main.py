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
def get_matches(db: Session):
    return db.query(Match).limit(10).all()

def create_match(db: Session, match: MatchSchema):
    db_match = Match(**match.dict())
    db.add(db_match)
    db.commit()
    return db_match

def get_deliveries(db: Session):
    return db.query(Delivery).limit(10).all()


def create_delivery(db: Session, delivery: DeliverySchema):
    db_delivery = Delivery(**delivery.dict())
    db.add(db_delivery)
    db.commit()
    return db_delivery


@router.get("/deliveries/")
def read_deliveries(db: Session = Depends(get_db)):
    return get_deliveries(db)

@router.post("/deliveries/")
def add_delivery(delivery: DeliverySchema, db: Session = Depends(get_db)):
    return create_delivery(db, delivery)


@router.get("/matches/")
def read_matches(db: Session = Depends(get_db)):
    return get_matches(db)

@router.post("/matches/")
def add_match(match: MatchSchema, db: Session = Depends(get_db)):
    return create_match(db, match)
    
from sqlalchemy.orm import Session
from sqlalchemy import func

@router.get("/batting_data/")
def get_batting_data(db: Session = Depends(get_db)):
    # Step 1: Get match IDs without limit
    match_ids = db.query(Match.id).order_by(Match.id).subquery()

    # Step 2: Join Deliveries and filter by those match IDs, then get top batters without limit
    results = (
        db.query(
            Delivery.batter,
            func.sum(Delivery.batsman_runs).label("total_runs"),
            func.count(Delivery.ball).label("total_balls")  # Count balls
        )
        .join(match_ids, Delivery.match_id == match_ids.c.id)
        .group_by(Delivery.batter)
        .order_by(func.sum(Delivery.batsman_runs).desc())
        .all()  # Removed limit here to get all data
    )

    if results:
        return [
            {"batter": row[0], "total_runs": row[1], "total_balls": row[2]}
            for row in results
        ]
    else:
        return {"message": "No data found"}


@router.get("/bowling_data/")
def get_bowling_data(db: Session = Depends(get_db)):
    # Step 1: Get match IDs
    match_ids = db.query(Match.id).order_by(Match.id).subquery()

    # Step 2: Join and calculate wickets (excluding run outs)
    results = (
        db.query(
            Delivery.bowler,
            func.count().label("total_wickets")
        )
        .filter(Delivery.match_id.in_(match_ids))
        .filter(Delivery.player_dismissed != None)
        .filter(Delivery.dismissal_kind != 'run out')
        .group_by(Delivery.bowler)
        .order_by(func.count().desc())
        .all()
    )

    if results:
        return [
            {"bowler": row[0], "total_wickets": row[1]}
            for row in results
        ]
    else:
        return {"message": "No data found"}



@router.get("/teams/stats/")
def get_teams_stats(db: Session = Depends(get_db)):
    # Get all distinct teams from team1 (only team1, not team2)
    teams = db.query(Match.team1).distinct().all()

    team_stats = []
    
    for team_tuple in teams:
        team = team_tuple[0]
        
        # Count matches played by this team
        matches_played = db.query(func.count()).filter(Match.team1 == team).scalar()

        team_stats.append({
            "teamname": team,
            "played": matches_played
        })

    return team_stats




@router.get("/players/stats/")
def get_players_stats(db: Session = Depends(get_db)):
    players = db.query(distinct(Delivery.batter)).union(
        db.query(distinct(Delivery.bowler)),
        db.query(distinct(Delivery.fielder))
    ).all()

    player_stats = []

    for player_tuple in players:
        player = player_tuple[0]

        # Match count
        match_ids_subq = db.query(distinct(Delivery.match_id)).filter(
            or_(
                Delivery.batter == player,
                Delivery.bowler == player,
                Delivery.fielder == player
            )
        ).subquery()

        match_count = db.query(func.count()).select_from(match_ids_subq).scalar()

        # Teams played for (based on role)
        batting_teams = db.query(distinct(Delivery.batting_team)).filter(
            Delivery.batter == player
        )

        bowling_teams = db.query(distinct(Delivery.bowling_team)).filter(
            Delivery.bowler == player
        )

        teams = batting_teams.union(bowling_teams).all()
        team_names = list(set([t[0] for t in teams]))

        # Batting
        batting_data = db.query(
            func.sum(Delivery.batsman_runs),
            func.count(Delivery.ball)
        ).filter(Delivery.batter == player).first()
        total_runs = batting_data[0] or 0
        total_balls = batting_data[1] or 0
        strike_rate = (total_runs / total_balls * 100) if total_balls > 0 else 0

        # Bowling
        total_wickets = db.query(func.count()).filter(
            Delivery.bowler == player,
            Delivery.player_dismissed != None,
            Delivery.dismissal_kind != 'run out'
        ).scalar() or 0

        # Fielding
        catches = db.query(func.count()).filter(
            Delivery.fielder == player,
            Delivery.dismissal_kind == 'caught'
        ).scalar() or 0

        runouts = db.query(func.count()).filter(
            Delivery.fielder == player,
            Delivery.dismissal_kind == 'run out'
        ).scalar() or 0

        # Color classification
        if total_runs >= 300 and total_wickets >= 10:
            role = "All-Rounder"
            color = "#FFD700"  # Gold
        elif total_runs >= 300:
            role = "Batter"
            color = "#00BFFF"  # DeepSkyBlue
        elif total_wickets >= 10:
            role = "Bowler"
            color = "#32CD32"  # LimeGreen
        else:
            role = "Other"
            color = "#D3D3D3"  # LightGray

        player_stats.append({
            "player": player,
            "teams": team_names,
            "matches_played": match_count,
            "total_runs": total_runs,
            "total_wickets": total_wickets,
            "strike_rate": round(strike_rate, 2),
            "catches": catches,
            "runouts": runouts,
            "role": role,
            "color": color
        })

    return player_stats
