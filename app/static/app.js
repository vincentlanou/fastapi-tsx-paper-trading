let currentTicker = "AAPL";
let currentPrice = 0.0;
let currentOrderType = "BUY";
let priceChartInstance = null;
let macdChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
    // Search form listener
    document.getElementById("searchBtn").addEventListener("click", () => {
        const val = document.getElementById("tickerInput").value.trim();
        if (val) loadTicker(val);
    });

    document.getElementById("tickerInput").addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            const val = document.getElementById("tickerInput").value.trim();
            if (val) loadTicker(val);
        }
    });

    // Initial load
    loadTicker("AAPL");
    refreshPortfolioAndHistory();
});

function showToast(msg, type = "success") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerText = msg;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

function loadTicker(ticker) {
    currentTicker = ticker.toUpperCase();
    document.getElementById("tickerInput").value = currentTicker;
    document.getElementById("tradeTicker").value = currentTicker;
    
    // Update chip active state
    document.querySelectorAll(".chip").forEach(chip => {
        if (chip.innerText === currentTicker) {
            chip.classList.add("active");
        } else {
            chip.classList.remove("active");
        }
    });

    fetchMarketData(currentTicker);
    fetchSentiment(currentTicker);
}

async function fetchMarketData(ticker) {
    try {
        const resp = await fetch(`/api/market/${ticker}`);
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || "Erreur de chargement des données de marché.");
        }
        const data = await resp.json();
        
        // Update price info
        currentPrice = data.current_price;
        document.getElementById("stockSymbol").innerText = data.ticker;
        document.getElementById("companyName").innerText = data.company_name || data.ticker;
        document.getElementById("stockPrice").innerText = `$${data.current_price.toFixed(2)}`;
        
        const changeEl = document.getElementById("priceChange");
        const isPos = data.price_change >= 0;
        changeEl.innerText = `${isPos ? '+' : ''}${data.price_change.toFixed(2)} (${isPos ? '+' : ''}${data.price_change_pct.toFixed(2)}%)`;
        changeEl.className = `change-val ${isPos ? 'pos' : 'neg'}`;

        // Indicators
        document.getElementById("momentumScore").innerText = `${data.indicators.momentum_score} / 100`;
        const sigEl = document.getElementById("momentumSignal");
        sigEl.innerText = data.indicators.overall_momentum_signal;
        sigEl.className = `badge-signal signal-${data.indicators.overall_momentum_signal.toLowerCase()}`;

        document.getElementById("rsiVal").innerText = `${data.indicators.current_rsi} (${data.indicators.rsi_status})`;
        document.getElementById("macdVal").innerText = `${data.indicators.current_macd} (${data.indicators.macd_status})`;

        calcTradeTotal();
        renderCharts(data.chart_data);

    } catch (err) {
        showToast(err.message, "error");
    }
}

async function fetchSentiment(ticker) {
    const summaryEl = document.getElementById("aiSummaryText");
    summaryEl.innerText = "Analyse de sentiment Gemini IA en cours...";
    
    try {
        const resp = await fetch(`/api/sentiment/${ticker}`);
        if (!resp.ok) throw new Error("Erreur lors de la récupération du sentiment IA.");
        const data = await resp.json();

        // Badge
        const sentBadge = document.getElementById("sentimentBadge");
        sentBadge.innerText = data.overall_sentiment;
        sentBadge.className = `badge-sentiment sentiment-${data.overall_sentiment.substring(0, 3).toLowerCase()}`;

        document.getElementById("sentimentScoreVal").innerText = Math.round(data.sentiment_score);
        document.getElementById("bullishScore").innerText = `${Math.round(data.bullish_score)}%`;
        document.getElementById("bearishScore").innerText = `${Math.round(data.bearish_score)}%`;

        document.getElementById("bullishBar").style.width = `${Math.round(data.bullish_score)}%`;
        document.getElementById("bearishBar").style.width = `${Math.round(data.bearish_score)}%`;

        summaryEl.innerText = data.ai_summary;

        // Key Drivers
        const driversList = document.getElementById("keyDriversList");
        driversList.innerHTML = "";
        (data.key_drivers || []).forEach(driver => {
            const li = document.createElement("li");
            li.innerText = driver;
            driversList.appendChild(li);
        });

        // Articles
        document.getElementById("newsCount").innerText = data.articles_analyzed_count || 0;
        const artList = document.getElementById("articlesList");
        artList.innerHTML = "";
        (data.articles || []).forEach(art => {
            const div = document.createElement("div");
            div.className = "article-item";
            div.innerHTML = `
                <a href="${art.link}" target="_blank" rel="noopener">${art.title}</a>
                <div class="article-meta">Source : ${art.publisher} | ${art.summary.substring(0, 100)}...</div>
            `;
            artList.appendChild(div);
        });

    } catch (err) {
        summaryEl.innerText = "Impossible de charger le sentiment Gemini pour le moment.";
    }
}

function renderCharts(chartData) {
    if (!chartData || chartData.length === 0) return;

    const labels = chartData.map(d => d.date);
    const prices = chartData.map(d => d.price);
    const rsis = chartData.map(d => d.rsi);
    const macds = chartData.map(d => d.macd);
    const hists = chartData.map(d => d.histogram);

    // Render Price + RSI Chart
    const ctx1 = document.getElementById("priceChart").getContext("2d");
    if (priceChartInstance) priceChartInstance.destroy();

    priceChartInstance = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Prix ($)',
                    data: prices,
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    tension: 0.2,
                    pointRadius: 0,
                    yAxisID: 'y'
                },
                {
                    label: 'RSI (14)',
                    data: rsis,
                    borderColor: '#8b5cf6',
                    borderWidth: 1.5,
                    borderDash: [4, 4],
                    pointRadius: 0,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: { legend: { labels: { color: '#9ca3af' } } },
            scales: {
                x: { ticks: { color: '#6b7280', maxTicksLimit: 8 }, grid: { color: 'rgba(255,255,255,0.04)' } },
                y: { type: 'linear', position: 'left', ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.04)' } },
                y1: { type: 'linear', position: 'right', min: 0, max: 100, ticks: { color: '#c084fc' }, grid: { drawOnChartArea: false } }
            }
        }
    });

    // Render MACD Histogram Chart
    const ctx2 = document.getElementById("macdChart").getContext("2d");
    if (macdChartInstance) macdChartInstance.destroy();

    macdChartInstance = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Histogramme MACD',
                    data: hists,
                    backgroundColor: hists.map(val => val >= 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(239, 68, 68, 0.7)'),
                    borderRadius: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { display: false }, grid: { display: false } },
                y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.04)' } }
            }
        }
    });
}

function setOrderType(type) {
    currentOrderType = type;
    const btnTabBuy = document.getElementById("tabBuy");
    const btnTabSell = document.getElementById("tabSell");
    const btnExec = document.getElementById("btnExecuteTrade");

    if (type === 'BUY') {
        btnTabBuy.classList.add("active");
        btnTabSell.classList.remove("active");
        btnExec.className = "btn-execute btn-buy";
        btnExec.innerText = "Simuler l'Achat";
    } else {
        btnTabSell.classList.add("active");
        btnTabBuy.classList.remove("active");
        btnExec.className = "btn-execute btn-sell";
        btnExec.innerText = "Simuler la Vente";
    }
}

function calcTradeTotal() {
    const qty = parseFloat(document.getElementById("tradeQty").value) || 0;
    const estPrice = currentPrice || 0;
    const total = qty * estPrice;

    document.getElementById("tradeEstPrice").innerText = `$${estPrice.toFixed(2)}`;
    document.getElementById("tradeEstTotal").innerText = `$${total.toFixed(2)}`;
}

async function executeTrade(e) {
    e.preventDefault();
    const qty = parseFloat(document.getElementById("tradeQty").value);
    if (!qty || qty <= 0) {
        showToast("Veuillez saisir une quantité valide.", "error");
        return;
    }

    const endpoint = currentOrderType === "BUY" ? "/api/trading/buy" : "/api/trading/sell";

    try {
        const resp = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ticker: currentTicker, quantity: qty })
        });

        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || "Échec de l'exécution de l'ordre.");

        showToast(`Ordre de ${currentOrderType} exécuté : ${qty} ${currentTicker} @ $${data.execution_price}`);
        document.getElementById("tradeQty").value = "";
        calcTradeTotal();
        refreshPortfolioAndHistory();

    } catch (err) {
        showToast(err.message, "error");
    }
}

async function refreshPortfolioAndHistory() {
    try {
        // Fetch Portfolio
        const portResp = await fetch("/api/trading/portfolio");
        if (portResp.ok) {
            const p = await portResp.json();

            document.getElementById("totalEquityVal").innerText = `$${p.total_equity.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;
            document.getElementById("cashBalanceVal").innerText = `$${p.cash_balance.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;

            const unPnlEl = document.getElementById("unrealizedPnlVal");
            const isUnPos = p.total_unrealized_pnl >= 0;
            unPnlEl.innerText = `${isUnPos ? '+' : ''}$${p.total_unrealized_pnl.toFixed(2)}`;
            unPnlEl.className = `metric-val ${isUnPos ? 'text-bullish' : 'text-bearish'}`;

            const rePnlEl = document.getElementById("realizedPnlVal");
            const isRePos = p.total_realized_pnl >= 0;
            rePnlEl.innerText = `${isRePos ? '+' : ''}$${p.total_realized_pnl.toFixed(2)}`;
            rePnlEl.className = `metric-val ${isRePos ? 'text-bullish' : 'text-bearish'}`;

            // Render Positions Table
            const tbody = document.getElementById("positionsTableBody");
            tbody.innerHTML = "";
            if (!p.positions || p.positions.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="empty-msg">Aucune position active dans le portefeuille.</td></tr>`;
            } else {
                p.positions.forEach(pos => {
                    const isPosPnl = pos.unrealized_pnl >= 0;
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><strong>${pos.ticker}</strong></td>
                        <td>${pos.quantity}</td>
                        <td>$${pos.average_buy_price.toFixed(2)}</td>
                        <td>$${pos.current_price.toFixed(2)}</td>
                        <td>$${pos.market_value.toFixed(2)}</td>
                        <td class="${isPosPnl ? 'text-bullish' : 'text-bearish'}">${isPosPnl ? '+' : ''}$${pos.unrealized_pnl.toFixed(2)} (${pos.unrealized_pnl_pct.toFixed(2)}%)</td>
                        <td><button onclick="quickSell('${pos.ticker}', ${pos.quantity})" class="btn-sm btn-danger-outline">Vendre</button></td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        }

        // Fetch History
        const histResp = await fetch("/api/trading/history");
        if (histResp.ok) {
            const history = await histResp.json();
            const tbodyHist = document.getElementById("historyTableBody");
            tbodyHist.innerHTML = "";

            if (!history || history.length === 0) {
                tbodyHist.innerHTML = `<tr><td colspan="7" class="empty-msg">Aucun ordre simulé pour l'instant.</td></tr>`;
            } else {
                history.forEach(t => {
                    const isBuy = t.order_type === "BUY";
                    const isRealizedPos = t.realized_pnl >= 0;
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><small>${t.executed_at}</small></td>
                        <td><span class="${isBuy ? 'badge-order-buy' : 'badge-order-sell'}">${t.order_type}</span></td>
                        <td><strong>${t.ticker}</strong></td>
                        <td>${t.quantity}</td>
                        <td>$${t.execution_price.toFixed(2)}</td>
                        <td>$${t.total_amount.toFixed(2)}</td>
                        <td class="${isRealizedPos ? 'text-bullish' : 'text-bearish'}">${!isBuy ? (isRealizedPos ? '+' : '') + '$' + t.realized_pnl.toFixed(2) : '-'}</td>
                    `;
                    tbodyHist.appendChild(tr);
                });
            }
        }

    } catch (err) {
        console.error("Error refreshing portfolio:", err);
    }
}

function quickSell(ticker, qty) {
    loadTicker(ticker);
    setOrderType("SELL");
    document.getElementById("tradeQty").value = qty;
    calcTradeTotal();
}

async function triggerTelegramTest() {
    try {
        const resp = await fetch("/api/notifications/test", { method: "POST" });
        const data = await resp.json();
        showToast(data.message, data.status === "sent" ? "success" : "error");
    } catch (err) {
        showToast("Erreur lors de l'envoi de la notification Telegram.", "error");
    }
}

async function resetPortfolio() {
    if (confirm("Voulez-vous vraiment réinitialiser votre portefeuille virtuel à $100,000 ? Toutes les positions et l'historique seront effacés.")) {
        try {
            const resp = await fetch("/api/trading/reset", { method: "POST" });
            if (resp.ok) {
                showToast("Portefeuille réinitialisé avec succès à $100,000.00 !");
                refreshPortfolioAndHistory();
            }
        } catch (err) {
            showToast("Erreur lors du reset du portefeuille.", "error");
        }
    }
}
