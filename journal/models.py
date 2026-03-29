from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from datetime import datetime
from .database import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Basic info
    pair = Column(String, default="GBPAUD")
    trade_date = Column(String)   # YYYY-MM-DD
    trade_time = Column(String)   # HH:MM
    direction = Column(String)    # "long" | "short"
    timeframe = Column(String, default="15m")

    # Checklist — each rule: "met" | "bent" | "not_met"
    rule_ema_cross = Column(String)
    rule_pullback_pips = Column(Float)
    rule_pullback_valid = Column(String)
    rule_touch_count = Column(Integer, default=2)   # 1 = single (bent), 2+ = clean
    rule_shift_candle_pips = Column(Float)
    rule_shift_candle_size = Column(String)          # met | bent | not_met
    rule_shift_candle_close = Column(String)         # did it close correct side of 13 EMA: met | bent
    rule_tdi_cross = Column(String)
    rule_tdi_black_side = Column(String)
    rule_tdi_yellow_side = Column(String)
    rule_tdi_trapped = Column(String)
    rule_shark_fin = Column(Boolean, default=False)  # True = shark fin present
    rule_dribble = Column(Boolean, default=False)    # True = dribble present
    rule_news_clear = Column(String)
    rule_session_valid = Column(String)

    # Bent rules — free text explaining any deviations
    rules_bent_notes = Column(String)

    # Entry details
    entry_price = Column(Float)
    stop_loss_pips = Column(Float)
    risk_percent = Column(Float, default=2.0)
    grade = Column(String)    # "A" | "B" | "C"

    # Outcome
    scenario = Column(Integer)        # 1 | 2 | 3 | 4
    exit_type = Column(String)        # "scratch" | "stop_hit" | "trailed" | "1r_locked"
    result_pips = Column(Float)       # positive = profit
    result_r = Column(Float)          # calculated R multiple

    # Notes
    notes = Column(String)
