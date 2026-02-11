from pydantic import BaseModel, Field


class DecayConfig(BaseModel):
    rate: float = 0.95
    reason_retention_days: int = 30


class ScoringWeights(BaseModel):
    signals: dict[str, float] = Field(default_factory=dict)
    decay: DecayConfig = Field(default_factory=DecayConfig)
    score_cap: float = 1000.0
