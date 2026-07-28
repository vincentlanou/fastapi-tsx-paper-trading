from fastapi import APIRouter, HTTPException
from app.schemas.sentiment import SentimentAnalysisResponse
from app.services.sentiment_service import get_news_sentiment

router = APIRouter(prefix="/api/sentiment", tags=["AI News Sentiment Analysis"])

@router.get("/{ticker}", response_model=SentimentAnalysisResponse)
def get_sentiment(ticker: str):
    """Analyze ticker financial news headlines using Gemini AI API."""
    try:
        return get_news_sentiment(ticker)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
