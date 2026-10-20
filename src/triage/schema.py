"""What the AI must return for every ticket. The API enforces this shape, so answers are always valid."""

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["billing", "payments", "domains", "checkout", "themes", "apps", "shipping", "account", "orders"]
Urgency = Literal["low", "medium", "high", "urgent"]
Sentiment = Literal["positive", "neutral", "frustrated", "angry"]
ChurnRisk = Literal["low", "medium", "high"]


class TriageResult(BaseModel):
    category: Category
    urgency: Urgency
    sentiment: Sentiment
    churn_risk: ChurnRisk
    reason: str = Field(description="One short sentence explaining the urgency and category, for the agent.")
