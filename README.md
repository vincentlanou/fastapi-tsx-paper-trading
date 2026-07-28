# QuantPulse - Plateforme de Paper Trading & Sentiment IA FastAPI

Application web complète et API REST pour l'analyse technique boursière via `yfinance` (indicateurs **RSI** + **MACD**), l'analyse de sentiment de news financières propulsée par **Gemini API**, un **Moteur de Paper Trading** basé sur **SQLite**, et des **Notifications Push Telegram Webhook**.

---

## 🚀 Fonctionnalités Principales

1. **Module Données de Marché & Momentum (`yfinance`)**
   - Récupération des cours boursiers en direct et données historiques pour tous les tickers (`AAPL`, `NVDA`, `TSLA`, `MSFT`, `BTC-USD`, etc.).
   - Calcul des indicateurs de momentum :
     - **RSI (14)** : Détection de surachat (≥ 70) et survente (≤ 30).
     - **MACD (12, 26, 9)** : Ligne MACD, Ligne de Signal et Histogramme de croisement.
   - Génération d'un **Score de Momentum** composite (0 à 100) et d'un signal global (`BULLISH`, `BEARISH`, `NEUTRAL`).

2. **Module Sentiment des News avec Gemini API**
   - Extraction des dernières actualités boursières via `yfinance`.
   - Analyse du sentiment par l'IA **Gemini API** avec retour structuré :
     - Score de sentiment (0 à 100), répartition Bullish / Bearish.
     - Synthèse IA en 2 phrases et facteurs catalysateurs clés.
     - Fallback d'analyseur de règles intégré en l'absence de clé API.

3. **Moteur de Paper Trading & Base SQLite**
   - Capital virtuel initial configurable (par défaut **$100,000.00**).
   - Simulations d'**Achat** et de **Vente** au prix de marché en direct.
   - Gestion du portefeuille :
     - Suivi du prix moyen d'achat et calcul du **P&L non réalisé** (positions).
     - Calcul du **P&L réalisé** lors des clôtures de vente.
     - Historique complet des ordres archivé dans la base SQLite.

4. **Notifications Push Telegram Webhook**
   - Notification instantanée formatée HTML envoyée sur Telegram dès qu'un trade virtuel est exécuté.
   - Journalisation console élégante si les clés Telegram ne sont pas configurées.

5. **Interface Dashboard Web Moderne & Sombre**
   - Design Glassmorphic sombre avec graphiques interactifs (Chart.js).
   - Barre de recherche de tickers et sélecteur rapide.
   - Formulaire d'ordre instantané et tableau de bord de portefeuille réactif.

---

## 🛠️ Installation et Lancement

### 1. Prérequis
- Python 3.10+

### 2. Démarrage du serveur FastAPI
```bash
python -m app.main
```
Ou avec `uvicorn` :
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Accès aux interfaces
- **Dashboard Web interactif** : [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Documentation OpenAPI (Swagger)** : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 Endpoints REST FastAPI

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/market/{ticker}` | Récupère le prix, le RSI, le MACD et le score de momentum |
| `GET` | `/api/sentiment/{ticker}` | Analyse le sentiment des news financières via Gemini API |
| `GET` | `/api/trading/portfolio` | Obtient le résumé du portefeuille virtuel, positions & P&L |
| `GET` | `/api/trading/history` | Obtient l'historique de tous les trades simulés |
| `POST` | `/api/trading/buy` | Simule un ordre d'Achat (Body: `{"ticker": "AAPL", "quantity": 10}`) |
| `POST` | `/api/trading/sell` | Simule un ordre de Vente (Body: `{"ticker": "AAPL", "quantity": 5}`) |
| `POST` | `/api/trading/reset` | Réinitialise le portefeuille virtuel à $100,000.00 |
| `POST` | `/api/notifications/test` | Déclenche une notification de test Telegram |

---

## 🧪 Exécution des Tests

```bash
python test_platform.py
```
