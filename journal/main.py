import os
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import engine, SessionLocal, Base
from .models import Trade

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ben's Trading Journal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class TradeCreate(BaseModel):
    pair: str = "GBPAUD"
    trade_date: str
    trade_time: str
    direction: str
    timeframe: str = "15m"

    rule_ema_cross: str
    rule_pullback_pips: Optional[float] = None
    rule_pullback_valid: str
    rule_touch_count: int = 2
    rule_shift_candle_pips: Optional[float] = None
    rule_shift_candle_size: str
    rule_shift_candle_close: str
    rule_tdi_cross: str
    rule_tdi_black_side: str
    rule_tdi_yellow_side: str
    rule_tdi_trapped: str
    rule_shark_fin: bool = False
    rule_dribble: bool = False
    rule_news_clear: str
    rule_session_valid: str
    rules_bent_notes: Optional[str] = None

    entry_price: Optional[float] = None
    stop_loss_pips: Optional[float] = None
    risk_percent: float = 2.0
    grade: str

    scenario: Optional[int] = None
    exit_type: Optional[str] = None
    result_pips: Optional[float] = None
    result_r: Optional[float] = None

    notes: Optional[str] = None


class TradeOut(BaseModel):
    id: int
    created_at: datetime
    pair: str
    trade_date: str
    trade_time: str
    direction: str
    timeframe: str
    rule_ema_cross: Optional[str]
    rule_pullback_pips: Optional[float]
    rule_pullback_valid: Optional[str]
    rule_touch_count: Optional[int]
    rule_shift_candle_pips: Optional[float]
    rule_shift_candle_size: Optional[str]
    rule_shift_candle_close: Optional[str]
    rule_tdi_cross: Optional[str]
    rule_tdi_black_side: Optional[str]
    rule_tdi_yellow_side: Optional[str]
    rule_tdi_trapped: Optional[str]
    rule_shark_fin: Optional[bool]
    rule_dribble: Optional[bool]
    rule_news_clear: Optional[str]
    rule_session_valid: Optional[str]
    rules_bent_notes: Optional[str]
    entry_price: Optional[float]
    stop_loss_pips: Optional[float]
    risk_percent: Optional[float]
    grade: Optional[str]
    scenario: Optional[int]
    exit_type: Optional[str]
    result_pips: Optional[float]
    result_r: Optional[float]
    notes: Optional[str]

    class Config:
        from_attributes = True


# ── Page routes ───────────────────────────────────────────────────────────────

@app.get("/")
def dashboard():
    return FileResponse(os.path.join(STATIC_DIR, "dashboard.html"))

@app.get("/log")
def log_page():
    return FileResponse(os.path.join(STATIC_DIR, "log.html"))

@app.get("/history")
def history_page():
    return FileResponse(os.path.join(STATIC_DIR, "history.html"))


# ── API routes ────────────────────────────────────────────────────────────────

@app.post("/api/trades", response_model=TradeOut)
def create_trade(payload: TradeCreate, db: Session = Depends(get_db)):
    data = payload.dict()
    # Auto-calculate R if not provided
    if data.get("result_r") is None and data.get("result_pips") is not None and data.get("stop_loss_pips"):
        data["result_r"] = round(data["result_pips"] / data["stop_loss_pips"], 2)
    trade = Trade(**data, created_at=datetime.utcnow())
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade


@app.get("/api/trades", response_model=List[TradeOut])
def list_trades(
    pair: Optional[str] = None,
    direction: Optional[str] = None,
    grade: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = db.query(Trade)
    if pair:
        q = q.filter(Trade.pair == pair)
    if direction:
        q = q.filter(Trade.direction == direction)
    if grade:
        q = q.filter(Trade.grade == grade)
    return q.order_by(Trade.trade_date.desc(), Trade.trade_time.desc()).offset(offset).limit(limit).all()


@app.get("/api/trades/{trade_id}", response_model=TradeOut)
def get_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@app.put("/api/trades/{trade_id}", response_model=TradeOut)
def update_trade(trade_id: int, payload: TradeCreate, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    for k, v in payload.dict().items():
        setattr(trade, k, v)
    if trade.result_pips is not None and trade.stop_loss_pips:
        trade.result_r = round(trade.result_pips / trade.stop_loss_pips, 2)
    db.commit()
    db.refresh(trade)
    return trade


@app.delete("/api/trades/{trade_id}")
def delete_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    db.delete(trade)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    trades = db.query(Trade).order_by(Trade.trade_date, Trade.trade_time).all()
    completed = [t for t in trades if t.result_r is not None]
    wins = [t for t in completed if t.result_r > 0]
    scratches = [t for t in completed if t.exit_type == "scratch"]

    def breakdown(field):
        result = {}
        for t in completed:
            val = str(getattr(t, field) or "unknown")
            if val not in result:
                result[val] = {"count": 0, "wins": 0, "total_r": 0.0}
            result[val]["count"] += 1
            if t.result_r > 0:
                result[val]["wins"] += 1
            result[val]["total_r"] = round(result[val]["total_r"] + t.result_r, 2)
        return result

    cumulative_r = 0.0
    equity_curve = []
    for t in completed:
        cumulative_r = round(cumulative_r + t.result_r, 2)
        equity_curve.append({
            "date": t.trade_date,
            "time": t.trade_time,
            "r": t.result_r,
            "cumulative_r": cumulative_r,
            "id": t.id,
        })

    return {
        "total_trades": len(trades),
        "completed": len(completed),
        "wins": len(wins),
        "scratches": len(scratches),
        "win_rate": round(len(wins) / len(completed) * 100, 1) if completed else 0,
        "avg_r": round(sum(t.result_r for t in completed) / len(completed), 2) if completed else 0,
        "total_pips": round(sum(t.result_pips or 0 for t in completed), 1),
        "total_r": round(sum(t.result_r for t in completed), 2),
        "by_grade": breakdown("grade"),
        "by_scenario": breakdown("scenario"),
        "by_direction": breakdown("direction"),
        "by_exit": breakdown("exit_type"),
        "equity_curve": equity_curve,
    }
