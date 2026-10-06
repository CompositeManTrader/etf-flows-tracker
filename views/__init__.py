"""Page views. Each module exposes render(ctx)."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Ctx:
    """Data + global sidebar selections shared by every page."""
    flows: pd.DataFrame
    history: pd.DataFrame
    status: pd.DataFrame
    monthly: pd.DataFrame
    session: pd.Timestamp | None
    categories: list[str] = field(default_factory=list)
    unit: str = "usd"  # "usd" | "pct"

    @property
    def valid(self) -> pd.DataFrame:
        """Valid flows restricted to the selected categories."""
        if self.flows.empty:
            return self.flows
        v = self.flows.dropna(subset=["flow_usd"])
        return v[v["category"].isin(self.categories)] if self.categories else v

    def day(self, session=None) -> pd.DataFrame:
        v = self.valid
        s = session if session is not None else self.session
        return v[v["date"] == s] if s is not None and not v.empty else v.iloc[0:0]

    @property
    def value_col(self) -> str:
        return "flow_pct_aum" if self.unit == "pct" else "flow_usd"
