from typing import List, Optional
from pydantic import BaseModel

class NewsArticle(BaseModel):
    title: str
    publisher: Optional[str] = "Market News"
    link: Optional[str] = "#"
    published_at: Optional[str] = None
    summary: Optional[str] = ""

class SentimentAnalysisResponse(BaseModel):
    ticker: str
    overall_sentiment: str # POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score: float # 0 to 100
    bullish_score: float   # 0 to 100
    bearish_score: float   # 0 to 100
    ai_summary: str
    key_drivers: List[str]
    articles_analyzed_count: int
    articles: List[NewsArticle]
    is_ai_powered: bool = True
