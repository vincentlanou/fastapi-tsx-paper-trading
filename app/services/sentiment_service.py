import json
import re
import yfinance as yf
from typing import List, Dict, Any
from app.config import GEMINI_API_KEY
from app.schemas.sentiment import SentimentAnalysisResponse, NewsArticle

def fetch_ticker_news(ticker: str, max_items: int = 6) -> List[NewsArticle]:
    """Fetch recent news articles for a ticker using yfinance."""
    yticker = yf.Ticker(ticker)
    raw_news = getattr(yticker, "news", []) or []
    
    articles = []
    for item in raw_news[:max_items]:
        # Handle yfinance news structure variations
        content = item.get("content", {}) if isinstance(item.get("content"), dict) else item
        title = content.get("title") or item.get("title") or "Financial Market Update"
        publisher = content.get("provider", {}).get("displayName") if isinstance(content.get("provider"), dict) else item.get("publisher", "Market News")
        link = content.get("canonicalUrl", {}).get("url") if isinstance(content.get("canonicalUrl"), dict) else item.get("link", "#")
        summary = content.get("summary") or item.get("summary") or title
        pub_date = content.get("pubDate") or item.get("providerPublishTime")
        
        articles.append(NewsArticle(
            title=title,
            publisher=publisher or "Market News",
            link=link or "#",
            published_at=str(pub_date) if pub_date else None,
            summary=summary
        ))
        
    if not articles:
        # Generic fallback news if ticker news is unavailable
        articles = [
            NewsArticle(
                title=f"{ticker} Market & Earnings Updates",
                publisher="Financial Digest",
                summary=f"Recent trading volume and market movements observed for {ticker}."
            )
        ]
    return articles

def analyze_sentiment_with_gemini(ticker: str, articles: List[NewsArticle]) -> SentimentAnalysisResponse:
    """Analyze news sentiment using Gemini API SDK."""
    if not GEMINI_API_KEY:
        return fallback_sentiment_analysis(ticker, articles, is_ai=False)
        
    news_text = "\n".join([f"- {a.title}: {a.summary}" for a in articles])
    
    prompt = f"""You are an expert financial analyst. Analyze the following news headlines and summaries for ticker symbol '{ticker}':

{news_text}

Provide your evaluation in strict JSON format with the following keys:
- "overall_sentiment": string ("POSITIVE", "NEGATIVE", or "NEUTRAL")
- "sentiment_score": float between 0.0 and 100.0 (overall positivity score)
- "bullish_score": float between 0.0 and 100.0
- "bearish_score": float between 0.0 and 100.0
- "ai_summary": string summarizing the financial narrative in 2 concise sentences
- "key_drivers": list of 3 short string bullet points highlighting major catalyst factors

Do NOT include any markdown code blocks (like ```json), just raw JSON object."""

    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        raw_text = response.text.strip()
        # Clean any markdown code blocks if returned
        raw_text = re.sub(r"^```json\s*", "", raw_text, flags=re.IGNORECASE)
        raw_text = re.sub(r"\s*```$", "", raw_text, flags=re.IGNORECASE).strip()
        
        data = json.loads(raw_text)
        
        return SentimentAnalysisResponse(
            ticker=ticker,
            overall_sentiment=data.get("overall_sentiment", "NEUTRAL").upper(),
            sentiment_score=float(data.get("sentiment_score", 50.0)),
            bullish_score=float(data.get("bullish_score", 50.0)),
            bearish_score=float(data.get("bearish_score", 50.0)),
            ai_summary=data.get("ai_summary", f"Financial news analysis for {ticker}."),
            key_drivers=data.get("key_drivers", ["Earnings outlook", "Market trends", "Volume dynamics"]),
            articles_analyzed_count=len(articles),
            articles=articles,
            is_ai_powered=True
        )
    except Exception as err:
        # Gracefully handle API errors or quota limits
        return fallback_sentiment_analysis(ticker, articles, is_ai=False, error_note=str(err))

def fallback_sentiment_analysis(ticker: str, articles: List[NewsArticle], is_ai: bool = False, error_note: str = "") -> SentimentAnalysisResponse:
    """Rule-based news sentiment evaluation fallback."""
    pos_words = {"growth", "gain", "surge", "record", "bull", "profit", "beat", "up", "high", "upgrade", "lead", "rally", "positive"}
    neg_words = {"fall", "drop", "loss", "decline", "bear", "miss", "down", "low", "downgrade", "risk", "warning", "negative", "slash"}
    
    pos_count = 0
    neg_count = 0
    
    for a in articles:
        text = (a.title + " " + (a.summary or "")).lower()
        pos_count += sum(1 for w in pos_words if w in text)
        neg_count += sum(1 for w in neg_words if w in text)
        
    total = pos_count + neg_count
    if total == 0:
        sentiment_score = 55.0
        bullish = 55.0
        bearish = 45.0
        sentiment = "NEUTRAL"
    else:
        bullish = (pos_count / total) * 100.0
        bearish = (neg_count / total) * 100.0
        sentiment_score = round(bullish, 1)
        if bullish > 55:
            sentiment = "POSITIVE"
        elif bearish > 55:
            sentiment = "NEGATIVE"
        else:
            sentiment = "NEUTRAL"
            
    summary = f"News sentiment for {ticker} is currently {sentiment.lower()} based on recent headlines."
    if error_note:
        summary += " (Using fallback news parser)."
        
    return SentimentAnalysisResponse(
        ticker=ticker,
        overall_sentiment=sentiment,
        sentiment_score=round(sentiment_score, 1),
        bullish_score=round(bullish, 1),
        bearish_score=round(bearish, 1),
        ai_summary=summary,
        key_drivers=[
            f"Headline keyword dynamics ({pos_count} positive signals, {neg_count} negative signals)",
            f"Recent news activity for {ticker}",
            "Market volatility & sentiment alignment"
        ],
        articles_analyzed_count=len(articles),
        articles=articles,
        is_ai_powered=is_ai
    )

def get_news_sentiment(ticker: str) -> SentimentAnalysisResponse:
    """Main entry point for sentiment analysis."""
    ticker_clean = ticker.strip().upper()
    articles = fetch_ticker_news(ticker_clean)
    return analyze_sentiment_with_gemini(ticker_clean, articles)
