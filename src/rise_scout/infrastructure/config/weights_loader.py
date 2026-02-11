from __future__ import annotations

import json
from pathlib import Path

from rise_scout.domain.scoring.weights import ScoringWeights

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[4] / "config" / "scoring_weights.json"


def load_weights(path: Path | None = None) -> ScoringWeights:
    config_path = path or DEFAULT_CONFIG_PATH
    with open(config_path) as f:
        data = json.load(f)
    return ScoringWeights.model_validate(data)
