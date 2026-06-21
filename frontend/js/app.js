const API_BASE = "/api/v1";

const state = {
    predictions: [],
    parlaySelections: [],
    connected: false,
};

function spinner(text = "Cargando...") {
    return `<div class="loading"><div class="spinner"></div>${text}</div>`;
}

function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icons = { error: "✕", success: "✓", info: "ℹ" };
    toast.innerHTML = `<span>${icons[type] || "ℹ"}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, 4000);
}

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initHamburger();
    loadDashboard();
    initParlayBuilder();
    loadFeatureImportance();
    checkConnection();

    document.getElementById("refreshBtn").addEventListener("click", loadDashboard);
    document.getElementById("groupFilter").addEventListener("change", applyFilters);
    document.getElementById("sortFilter").addEventListener("change", applyFilters);
    document.getElementById("searchInput").addEventListener("input", applyFilters);
    document.getElementById("safestSizeFilter").addEventListener("change", loadSafestParlays);
    document.getElementById("loadMarketsBtn").addEventListener("click", loadMarkets);
});

// ─────────── CONNECTION ───────────

async function checkConnection() {
    const banner = document.getElementById("connectionBanner");
    try {
        const res = await fetch(`${API_BASE}/matches`);
        if (res.ok) {
            banner.style.display = "none";
            state.connected = true;
            loadDashboard();
            return true;
        }
    } catch {
        banner.style.display = "flex";
        state.connected = false;
    }
    return false;
}

async function fetchAPI(endpoint, options = {}) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            headers: { "Content-Type": "application/json" },
            ...options,
        });
        if (!res.ok) {
            const body = await res.text().catch(() => "");
            throw new Error(`HTTP ${res.status}: ${body.slice(0, 80)}`);
        }
        state.connected = true;
        document.getElementById("connectionBanner").style.display = "none";
        return await res.json();
    } catch (err) {
        console.error(`API error (${endpoint}):`, err);
        if (!state.connected) {
            document.getElementById("connectionBanner").style.display = "flex";
        }
        showToast(`Error al cargar: ${err.message}`, "error");
        return null;
    }
}

// ─────────── HAMBURGER ───────────

function initHamburger() {
    const btn = document.getElementById("hamburgerBtn");
    const links = document.getElementById("navLinks");
    if (!btn) return;
    btn.addEventListener("click", () => {
        links.classList.toggle("open");
    });
    document.querySelectorAll(".nav-btn").forEach(nb => {
        nb.addEventListener("click", () => links.classList.remove("open"));
    });
}

// ─────────── NAVIGATION ───────────

function initNavigation() {
    document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".nav-btn, .tab-content").forEach(el => el.classList.remove("active"));
            btn.classList.add("active");
            const tab = document.getElementById(`tab-${btn.dataset.tab}`);
            tab.classList.add("active");
            if (btn.dataset.tab === "safest") loadSafestParlays();
            if (btn.dataset.tab === "models") loadFeatureImportance();
            if (btn.dataset.tab === "dashboard") loadDashboard();
            if (btn.dataset.tab === "detalles") loadDetails();
            if (btn.dataset.tab === "markets") loadMarkets();
        });
    });
}

// ─────────── DASHBOARD ───────────

async function loadDashboard() {
    const container = document.getElementById("matchesContainer");
    container.innerHTML = spinner("Cargando partidos...");

    const data = await fetchAPI("/predictions");
    if (!data?.predictions) {
        container.innerHTML = '<div class="loading">Error al cargar datos. Verifica que el backend esté corriendo en localhost:8000.</div>';
        return;
    }

    state.predictions = data.predictions;
    applyFilters();
}

function scoreSortKey(p) {
    const scores = [p.probabilities.home, p.probabilities.draw, p.probabilities.away];
    return Math.max(...scores);
}

function applyFilters() {
    const search = document.getElementById("searchInput").value.toLowerCase();
    const group = document.getElementById("groupFilter").value;
    const sort = document.getElementById("sortFilter").value;
    let filtered = state.predictions;
    if (search) {
        filtered = filtered.filter(p =>
            p.home_team.toLowerCase().includes(search) ||
            p.away_team.toLowerCase().includes(search)
        );
    }
    if (group !== "all") filtered = filtered.filter(p => p.group === group);
    if (sort === "confidence-desc") filtered.sort((a, b) => scoreSortKey(b) - scoreSortKey(a));
    else if (sort === "date") filtered.sort((a, b) => (a.date || "").localeCompare(b.date || ""));
    else if (sort === "team") filtered.sort((a, b) => a.home_team.localeCompare(b.home_team));
    renderMatches(filtered);
}

function renderModelDetails(p) {
    if (!p.model_details) return "";
    const models = p.model_details;
    return Object.entries(models).map(([name, probs]) =>
        `<div class="model-compact-item">
            <span class="model-name">${name.replace("_", " ")}</span>
            <span class="model-probs">${probs.home} / ${probs.draw} / ${probs.away}</span>
        </div>`
    ).join("");
}

function modelBarClass(val) {
    if (val >= 40) return "green";
    if (val >= 25) return "yellow";
    return "red";
}

function renderMatches(predictions) {
    const container = document.getElementById("matchesContainer");
    if (!predictions.length) {
        container.innerHTML = '<div class="empty-state">No se encontraron partidos.</div>';
        return;
    }

    container.innerHTML = predictions.map((p, i) => `
        <div class="match-card">
            <div class="match-header">
                <span>${p.group ? "Grupo " + p.group : ""}</span>
                <span>${p.date || ""}</span>
            </div>
            <div class="match-teams">
                <div class="team">
                    <span class="team-name">${p.home_team}</span>
                </div>
                <span class="vs">VS</span>
                <div class="team">
                    <span class="team-name">${p.away_team}</span>
                </div>
            </div>
            <div class="prediction-bars">
                <div class="prob-home" style="width:${p.probabilities.home}%"></div>
                <div class="prob-draw" style="width:${p.probabilities.draw}%"></div>
                <div class="prob-away" style="width:${p.probabilities.away}%"></div>
            </div>
            <div class="probabilities">
                <div class="prob-item">
                    <div class="prob-value" style="color:var(--accent-green)">${p.probabilities.home}%</div>
                    <div class="prob-label">Local (1)</div>
                </div>
                <div class="prob-item">
                    <div class="prob-value" style="color:var(--accent-yellow)">${p.probabilities.draw}%</div>
                    <div class="prob-label">Empate (X)</div>
                </div>
                <div class="prob-item">
                    <div class="prob-value" style="color:var(--accent-red)">${p.probabilities.away}%</div>
                    <div class="prob-label">Visitante (2)</div>
                </div>
            </div>
            <div class="match-stats-compact">
                <div class="stats-grid">
                    <div class="stat-cell">
                        <span class="stat-cell-title">Posesión</span>
                        <div class="stat-cell-row">
                            <span class="stat-num" style="color:var(--accent-green)">${p.stats?.possession?.home ?? "-"}%</span>
                            <div class="stat-bar-outter"><div class="stat-bar-inner stat-bar-pos" style="width:${p.stats?.possession?.home ?? 50}%"></div></div>
                            <span class="stat-vs">vs</span>
                            <div class="stat-bar-outter"><div class="stat-bar-inner" style="width:${p.stats?.possession?.away ?? 50}%;background:var(--accent-red)"></div></div>
                            <span class="stat-num" style="color:var(--accent-red)">${p.stats?.possession?.away ?? "-"}%</span>
                        </div>
                    </div>
                    <div class="stat-cell">
                        <span class="stat-cell-title">Tiros totales</span>
                        <div class="stat-cell-row">
                            <span class="stat-num">${p.stats?.shots_total?.home ?? "-"}</span>
                            <span class="stat-vs">vs</span>
                            <span class="stat-num">${p.stats?.shots_total?.away ?? "-"}</span>
                        </div>
                    </div>
                    <div class="stat-cell">
                        <span class="stat-cell-title">Tiros al arco</span>
                        <div class="stat-cell-row">
                            <span class="stat-num">${p.stats?.shots_on_target?.home ?? "-"}</span>
                            <span class="stat-vs">vs</span>
                            <span class="stat-num">${p.stats?.shots_on_target?.away ?? "-"}</span>
                        </div>
                    </div>
                    <div class="stat-cell">
                        <span class="stat-cell-title">Faltas</span>
                        <div class="stat-cell-row">
                            <span class="stat-num">${p.stats?.fouls?.home ?? "-"}</span>
                            <span class="stat-vs">vs</span>
                            <span class="stat-num">${p.stats?.fouls?.away ?? "-"}</span>
                        </div>
                    </div>
                    <div class="stat-cell">
                        <span class="stat-cell-title">T. Amarillas</span>
                        <div class="stat-cell-row">
                            <span class="stat-num" style="color:var(--accent-yellow)">${p.stats?.yellow_cards?.home ?? "-"}</span>
                            <span class="stat-vs">vs</span>
                            <span class="stat-num" style="color:var(--accent-yellow)">${p.stats?.yellow_cards?.away ?? "-"}</span>
                        </div>
                    </div>
                    <div class="stat-cell">
                        <span class="stat-cell-title">T. Rojas</span>
                        <div class="stat-cell-row">
                            <span class="stat-num">${p.stats?.red_cards?.home ?? "-"}</span>
                            <span class="stat-vs">vs</span>
                            <span class="stat-num">${p.stats?.red_cards?.away ?? "-"}</span>
                        </div>
                    </div>
                    <div class="stat-cell">
                        <span class="stat-cell-title">Córners</span>
                        <div class="stat-cell-row">
                            <span class="stat-num">${p.stats?.corners?.home ?? "-"}</span>
                            <span class="stat-vs">vs</span>
                            <span class="stat-num">${p.stats?.corners?.away ?? "-"}</span>
                        </div>
                    </div>
                    <div class="stat-cell">
                        <span class="stat-cell-title">Offsides</span>
                        <div class="stat-cell-row">
                            <span class="stat-num">${p.stats?.offsides?.home ?? "-"}</span>
                            <span class="stat-vs">vs</span>
                            <span class="stat-num">${p.stats?.offsides?.away ?? "-"}</span>
                        </div>
                    </div>
                    <div class="stat-cell">
                        <span class="stat-cell-title">Atajadas</span>
                        <div class="stat-cell-row">
                            <span class="stat-num">${p.stats?.saves?.home ?? "-"}</span>
                            <span class="stat-vs">vs</span>
                            <span class="stat-num">${p.stats?.saves?.away ?? "-"}</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="match-stats">
                <div class="stat-item">
                    <span class="stat-label">BTTS
                        <span class="info-icon">?
                            <span class="info-tooltip">Ambos equipos anotan (Both Teams To Score)</span>
                        </span>
                    </span>
                    <span class="stat-value">${p.btts_probability}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Over 2.5
                        <span class="info-icon">?
                            <span class="info-tooltip">Más de 2.5 goles totales en el partido</span>
                        </span>
                    </span>
                    <span class="stat-value">${p.over_25_probability}%</span>
                </div>
            </div>
            <div class="safest-pick ${confidenceClass(p.confidence)}">
                <span>Pick: ${pickLabel(p.safest_pick)}
                    <span class="info-icon">?
                        <span class="info-tooltip">Resultado más probable según el ensemble ponderado de los 4 modelos</span>
                    </span>
                </span>
                <span class="pick-badge">${p.confidence}%</span>
            </div>
            ${p.model_details ? `<button class="expand-btn" onclick="toggleDetails(this)">📊 Ver detalles por modelo</button>
            <div class="model-details">
                <div class="model-compact-grid">${renderModelDetails(p)}</div>
            </div>` : ""}
        </div>
    `).join("");
}

function toggleDetails(btn) {
    const details = btn.nextElementSibling;
    const isOpen = details.classList.toggle("open");
    btn.textContent = isOpen ? "📊 Ocultar detalles" : "📊 Ver detalles por modelo";
}

// ─────────── DETALLES TAB ───────────

async function loadDetails() {
    const container = document.getElementById("detailsContainer");
    container.innerHTML = spinner("Cargando predicciones detalladas...");

    if (!state.predictions.length) {
        const data = await fetchAPI("/predictions");
        if (!data?.predictions) {
            container.innerHTML = '<div class="empty-state">Error al cargar datos.</div>';
            return;
        }
        state.predictions = data.predictions;
    }

    renderDetails(state.predictions);

    document.getElementById("detailGroupFilter").addEventListener("change", filterDetails);
    document.getElementById("detailSortFilter").addEventListener("change", filterDetails);
}

function filterDetails() {
    if (!state.predictions.length) return;
    const group = document.getElementById("detailGroupFilter").value;
    const sort = document.getElementById("detailSortFilter").value;
    let filtered = state.predictions;
    if (group !== "all") filtered = filtered.filter(p => p.group === group);
    if (sort === "confidence-desc") filtered.sort((a, b) => scoreSortKey(b) - scoreSortKey(a));
    else if (sort === "date") filtered.sort((a, b) => (a.date || "").localeCompare(b.date || ""));
    else if (sort === "team") filtered.sort((a, b) => a.home_team.localeCompare(b.home_team));
    renderDetails(filtered);
}

function renderDetails(predictions) {
    const container = document.getElementById("detailsContainer");
    if (!predictions.length) {
        container.innerHTML = '<div class="empty-state">No se encontraron partidos.</div>';
        return;
    }

    container.innerHTML = predictions.map((p, i) => {
        const models = p.model_details || {};
        const modelNames = Object.keys(models);
        const safeKey = `fullpred_${i}`.replace(/[^a-zA-Z0-9]/g, "_");
        return `
        <div class="details-card">
            <div class="details-header">
                <span>${p.group ? "Grupo " + p.group : ""}</span>
                <span>${p.date || ""}</span>
            </div>
            <div class="details-teams">${p.home_team} vs ${p.away_team}</div>
            <div class="model-comparison">
                ${modelNames.map(name => {
                    const m = models[name];
                    return `
                    <div class="model-col">
                        <div class="model-col-title">${name.replace("_", " ")}</div>
                        <div class="prob prob-1">${m.home}%</div>
                        <div class="prob-bar"><div class="prob-bar-fill ${modelBarClass(m.home)}" style="width:${m.home}%"></div></div>
                        <div class="prob prob-x">${m.draw}%</div>
                        <div class="prob-bar"><div class="prob-bar-fill ${modelBarClass(m.draw)}" style="width:${m.draw}%"></div></div>
                        <div class="prob prob-2">${m.away}%</div>
                        <div class="prob-bar"><div class="prob-bar-fill ${modelBarClass(m.away)}" style="width:${m.away}%"></div></div>
                    </div>`;
                }).join("")}
            </div>
            <hr class="stats-divider">
            <div class="stats-grid">
                <div class="stat-cell">
                    <span class="stat-cell-title">Posesión</span>
                    <div class="stat-cell-row">
                        <span class="stat-num" style="color:var(--accent-green)">${p.stats?.possession?.home ?? "-"}%</span>
                        <div class="stat-bar-outter"><div class="stat-bar-inner stat-bar-pos" style="width:${p.stats?.possession?.home ?? 50}%"></div></div>
                        <span class="stat-vs">vs</span>
                        <div class="stat-bar-outter"><div class="stat-bar-inner" style="width:${p.stats?.possession?.away ?? 50}%;background:var(--accent-red)"></div></div>
                        <span class="stat-num" style="color:var(--accent-red)">${p.stats?.possession?.away ?? "-"}%</span>
                    </div>
                </div>
                <div class="stat-cell">
                    <span class="stat-cell-title">Tiros totales</span>
                    <div class="stat-cell-row">
                        <span class="stat-num">${p.stats?.shots_total?.home ?? "-"}</span>
                        <span class="stat-vs">vs</span>
                        <span class="stat-num">${p.stats?.shots_total?.away ?? "-"}</span>
                    </div>
                </div>
                <div class="stat-cell">
                    <span class="stat-cell-title">Tiros al arco</span>
                    <div class="stat-cell-row">
                        <span class="stat-num">${p.stats?.shots_on_target?.home ?? "-"}</span>
                        <span class="stat-vs">vs</span>
                        <span class="stat-num">${p.stats?.shots_on_target?.away ?? "-"}</span>
                    </div>
                </div>
                <div class="stat-cell">
                    <span class="stat-cell-title">Faltas</span>
                    <div class="stat-cell-row">
                        <span class="stat-num">${p.stats?.fouls?.home ?? "-"}</span>
                        <span class="stat-vs">vs</span>
                        <span class="stat-num">${p.stats?.fouls?.away ?? "-"}</span>
                    </div>
                </div>
                <div class="stat-cell">
                    <span class="stat-cell-title">T. Amarillas</span>
                    <div class="stat-cell-row">
                        <span class="stat-num" style="color:var(--accent-yellow)">${p.stats?.yellow_cards?.home ?? "-"}</span>
                        <span class="stat-vs">vs</span>
                        <span class="stat-num" style="color:var(--accent-yellow)">${p.stats?.yellow_cards?.away ?? "-"}</span>
                    </div>
                </div>
                <div class="stat-cell">
                    <span class="stat-cell-title">T. Rojas</span>
                    <div class="stat-cell-row">
                        <span class="stat-num">${p.stats?.red_cards?.home ?? "-"}</span>
                        <span class="stat-vs">vs</span>
                        <span class="stat-num">${p.stats?.red_cards?.away ?? "-"}</span>
                    </div>
                </div>
                <div class="stat-cell">
                    <span class="stat-cell-title">Córners</span>
                    <div class="stat-cell-row">
                        <span class="stat-num">${p.stats?.corners?.home ?? "-"}</span>
                        <span class="stat-vs">vs</span>
                        <span class="stat-num">${p.stats?.corners?.away ?? "-"}</span>
                    </div>
                </div>
                <div class="stat-cell">
                    <span class="stat-cell-title">Offsides</span>
                    <div class="stat-cell-row">
                        <span class="stat-num">${p.stats?.offsides?.home ?? "-"}</span>
                        <span class="stat-vs">vs</span>
                        <span class="stat-num">${p.stats?.offsides?.away ?? "-"}</span>
                    </div>
                </div>
                <div class="stat-cell">
                    <span class="stat-cell-title">Atajadas</span>
                    <div class="stat-cell-row">
                        <span class="stat-num">${p.stats?.saves?.home ?? "-"}</span>
                        <span class="stat-vs">vs</span>
                        <span class="stat-num">${p.stats?.saves?.away ?? "-"}</span>
                    </div>
                </div>
            </div>
            <hr class="stats-divider">
            <div class="details-btts">
                <span>BTTS: <strong>${p.btts_probability}%</strong></span>
                <span>Over 2.5: <strong>${p.over_25_probability}%</strong></span>
                <span>Pick: <strong style="color:${p.confidence >= 55 ? "var(--accent-green)" : p.confidence >= 40 ? "var(--accent-yellow)" : "var(--accent-red)"}">${pickLabel(p.safest_pick)} (${p.confidence}%)</strong></span>
            </div>
            <button class="expand-btn" onclick="loadFullPrediction(this, '${encodeURIComponent(p.home_team)}', '${encodeURIComponent(p.away_team)}', '${safeKey}')">🎯 Ver Predicción Completa + Mercados + Parlay</button>
            <div id="${safeKey}" class="model-details"></div>
        </div>`;
    }).join("");
}

function pickLabel(pick) {
    return { "1": "1 (Local)", "X": "X (Empate)", "2": "2 (Visitante)" }[pick] || pick;
}

function confidenceClass(conf) {
    if (conf >= 55) return "high";
    if (conf >= 40) return "medium";
    return "low";
}

// ─────────── FULL PREDICTION ───────────

async function loadFullPrediction(btn, home, away, containerId) {
    const container = document.getElementById(containerId);
    const isOpen = container.classList.toggle("open");
    if (!isOpen) { btn.textContent = "🎯 Ver Predicción Completa + Mercados + Parlay"; return; }
    btn.textContent = "Cargando...";
    container.innerHTML = spinner();

    const data = await fetchAPI(`/predictions/${home}/${away}/full`);
    if (!data) {
        container.innerHTML = '<div class="empty-state">Error al cargar.</div>';
        btn.textContent = "🎯 Ver Predicción Completa";
        return;
    }

    btn.textContent = "🎯 Ocultar Predicción Completa";
    container.innerHTML = renderFullPrediction(data);
}

function renderFullPrediction(d) {
    const p = d.prediction;
    const stats = d.stats;
    const mkts = d.markets || [];
    const hp = d.player_stats?.home || [];
    const ap = d.player_stats?.away || [];
    const parlay = d.suggested_parlay;

    const top5 = mkts.filter(m => m.probability >= 50).slice(0, 8);

    let html = `
    <div style="margin-top:0.5rem">
        <h4 style="font-size:0.82rem;margin-bottom:0.4rem;color:var(--accent-blue)">📊 Mercados Estadísticos</h4>
        <div class="market-list">
            ${top5.map(m => `
                <div class="market-item">
                    <span class="market-name">${m.label || m.market}</span>
                    <span class="market-prob ${probClass(m.probability)}">${m.probability}%</span>
                </div>
            `).join("")}
        </div>`;

    if (parlay?.picks?.length >= 2) {
        html += `
        <hr class="stats-divider">
        <h4 style="font-size:0.82rem;margin-bottom:0.4rem;color:var(--accent-green)">🎲 Parlay Sugerido para este Partido</h4>
        ${parlay.picks.map(m => `
            <div class="stat-parlay-pick" style="font-size:0.72rem">
                <span class="pick-market">${m.label || m.market}</span>
                <span class="pick-prob">${m.probability}%</span>
            </div>
        `).join("")}
        <div style="text-align:right;font-size:0.8rem;font-weight:700;color:var(--accent-green);margin-top:0.3rem">
            Combinado: ${parlay.combined_probability}%
        </div>`;
    }

    html += `
        <hr class="stats-divider">
        <h4 style="font-size:0.82rem;margin-bottom:0.4rem;color:var(--accent-yellow)">👥 ${d.match.home_team} — Distribución por Jugador</h4>
        <div style="font-size:0.65rem;overflow-x:auto">
        <table style="width:100%;border-collapse:collapse">
            <tr style="color:var(--text-secondary)">
                <th style="text-align:left;padding:0.2rem 0.3rem">Jugador</th>
                <th style="padding:0.2rem 0.3rem">Tiros</th>
                <th style="padding:0.2rem 0.3rem">T.Arco</th>
                <th style="padding:0.2rem 0.3rem">Faltas</th>
                <th style="padding:0.2rem 0.3rem">T.Amar</th>
                <th style="padding:0.2rem 0.3rem">Entradas</th>
                <th style="padding:0.2rem 0.3rem">F.Recib</th>
            </tr>
            ${hp.filter(x => x.position !== "GK").map(pl => `
                <tr style="border-top:1px solid var(--border)">
                    <td style="padding:0.15rem 0.3rem">${pl.name} <span style="color:var(--text-secondary)">${pl.position}</span></td>
                    <td style="text-align:center;padding:0.15rem 0.3rem">${pl.shots}</td>
                    <td style="text-align:center;padding:0.15rem 0.3rem">${pl.sot}</td>
                    <td style="text-align:center;padding:0.15rem 0.3rem">${pl.fouls}</td>
                    <td style="text-align:center;padding:0.15rem 0.3rem;color:var(--accent-yellow)">${pl.yc || "-"}</td>
                    <td style="text-align:center;padding:0.15rem 0.3rem">${pl.tackles}</td>
                    <td style="text-align:center;padding:0.15rem 0.3rem">${pl.fouls_suffered}</td>
                </tr>
            `).join("")}
        </table>
        </div>

        <hr class="stats-divider">
        <h4 style="font-size:0.82rem;margin-bottom:0.4rem;color:var(--accent-yellow)">👥 ${d.match.away_team} — Distribución por Jugador</h4>
        <div style="font-size:0.65rem;overflow-x:auto">
        <table style="width:100%;border-collapse:collapse">
            <tr style="color:var(--text-secondary)">
                <th style="text-align:left;padding:0.2rem 0.3rem">Jugador</th>
                <th style="padding:0.2rem 0.3rem">Tiros</th>
                <th style="padding:0.2rem 0.3rem">T.Arco</th>
                <th style="padding:0.2rem 0.3rem">Faltas</th>
                <th style="padding:0.2rem 0.3rem">T.Amar</th>
                <th style="padding:0.2rem 0.3rem">Entradas</th>
                <th style="padding:0.2rem 0.3rem">F.Recib</th>
            </tr>
            ${ap.filter(x => x.position !== "GK").map(pl => `
                <tr style="border-top:1px solid var(--border)">
                    <td style="padding:0.15rem 0.3rem">${pl.name} <span style="color:var(--text-secondary)">${pl.position}</span></td>
                    <td style="text-align:center;padding:0.15rem 0.3rem">${pl.shots}</td>
                    <td style="text-align:center;padding:0.15rem 0.3rem">${pl.sot}</td>
                    <td style="text-align:center;padding:0.15rem 0.3rem">${pl.fouls}</td>
                    <td style="text-align:center;padding:0.15rem 0.3rem;color:var(--accent-yellow)">${pl.yc || "-"}</td>
                    <td style="text-align:center;padding:0.15rem 0.3rem">${pl.tackles}</td>
                    <td style="text-align:center;padding:0.15rem 0.3rem">${pl.fouls_suffered}</td>
                </tr>
            `).join("")}
        </table>
        </div>
    </div>`;

    return html;
}

// ─────────── MARKETS TAB ───────────

function probClass(val) {
    if (val >= 65) return "high";
    if (val >= 50) return "med";
    return "low";
}

async function loadMarkets() {
    const container = document.getElementById("marketsContainer");
    container.innerHTML = spinner("Cargando mercados...");
    document.getElementById("statParlayResult").style.display = "none";

    const data = await fetchAPI("/predictions");
    if (!data?.predictions) {
        container.innerHTML = '<div class="empty-state">Error al cargar datos.</div>';
        return;
    }

    const matchData = await fetchAPI("/matches");
    const matches = matchData?.matches || [];

    let html = "";
    for (const p of data.predictions) {
        const m = matches.find(x => x.home === p.home_team && x.away === p.away_team);
        const res = await fetchAPI(`/markets/${encodeURIComponent(p.home_team)}/${encodeURIComponent(p.away_team)}`);
        if (!res?.markets) continue;

        const top = res.markets.filter(mk => mk.probability >= 50).slice(0, 8);
        html += `
        <div class="market-match-card">
            <div class="market-match-title">${p.home_team} vs ${p.away_team}</div>
            <div class="market-match-meta">${p.group ? "Grupo " + p.group : ""} | ${p.date || ""} ${m?.score ? "| " + m.score.home + "-" + m.score.away : ""}</div>
            <div class="market-list">
                ${top.map(mk => `
                    <div class="market-item">
                        <span class="market-name">${mk.label || mk.market.replace(/_/g, " ").toUpperCase()}</span>
                        <span class="market-prob ${probClass(mk.probability)}">${mk.probability}%</span>
                    </div>
                `).join("")}
            </div>
        </div>`;
    }

    container.innerHTML = html || '<div class="empty-state">No hay mercados disponibles.</div>';

    document.getElementById("buildStatParlayBtn").onclick = buildStatParlay;
}

async function buildStatParlay() {
    const container = document.getElementById("statParlayResult");
    container.style.display = "block";
    container.innerHTML = spinner("Buscando combinaciones seguras...");

    const data = await fetchAPI("/parlay/statistical?min_prob=65&max_legs=4");
    if (!data?.suggestions?.length) {
        container.innerHTML = '<h3>Parlay Estadístico</h3><p class="empty-state">No se encontraron combinaciones con suficiente probabilidad.</p>';
        return;
    }

    container.innerHTML = `
        <h3>🎲 Parlay Estadístico Seguro</h3>
        <p style="font-size:0.82rem;color:var(--text-secondary);margin-bottom:0.75rem">
            Basado en perfiles estadísticos de cada selección (${data.total_picks_found} mercados disponibles en total).
        </p>
        ${data.suggestions.map(s => `
            <div class="stat-parlay-pick">
                <div>
                    <div class="pick-market">${s.label || s.market.replace(/_/g, " ").toUpperCase()}</div>
                    <div class="pick-match">${s.match} (${s.date || ""})</div>
                </div>
                <span class="pick-prob">${s.probability}%</span>
            </div>
        `).join("")}
        <div style="margin-top:0.75rem;padding-top:0.6rem;border-top:1px solid var(--border);
                    display:flex;justify-content:space-between;align-items:center">
            <span style="color:var(--text-secondary);font-size:0.85rem">Probabilidad Combinada</span>
            <span style="font-size:1.3rem;font-weight:700;color:var(--accent-green)">${data.combined_probability}%</span>
        </div>
    `;
}

// ─────────── PARLAY BUILDER ───────────

function initParlayBuilder() {
    document.getElementById("addSelectionBtn").addEventListener("click", addSelectionRow);
    document.getElementById("calculateParlayBtn").addEventListener("click", calculateParlay);
}

async function getTeamOptions() {
    const data = await fetchAPI("/matches");
    if (!data?.matches) return [];
    const teams = new Set();
    data.matches.forEach(m => { teams.add(m.home); teams.add(m.away); });
    return Array.from(teams).sort();
}

async function getMatchesForTeam(team) {
    const data = await fetchAPI("/matches");
    if (!data?.matches) return [];
    return data.matches.filter(m => m.home === team || m.away === team);
}

let selectionCounter = 0;

async function addSelectionRow() {
    const container = document.getElementById("parlaySelections");
    const idx = selectionCounter++;
    const teams = await getTeamOptions();

    const div = document.createElement("div");
    div.className = "selection-row";
    div.dataset.index = idx;

    const teamOpts = teams.map(t => `<option value="${t}">${t}</option>`).join("");

    div.innerHTML = `
        <div class="field">
            <label>Partido</label>
            <select class="parlay-home">${teamOpts}</select>
        </div>
        <div class="field">
            <label>vs</label>
            <select class="parlay-away"><option value="">Seleccionar...</option></select>
        </div>
        <div class="field field-small">
            <label>Pick</label>
            <select class="parlay-pick">
                <option value="1">1 - Local</option>
                <option value="X">X - Empate</option>
                <option value="2">2 - Visitante</option>
            </select>
        </div>
        <div class="field field-small">
            <label>Cuota</label>
            <input type="number" class="parlay-odds" step="0.01" min="1.01" placeholder="2.10">
        </div>
        <button class="remove-btn">✕</button>
    `;

    const homeSelect = div.querySelector(".parlay-home");
    const awaySelect = div.querySelector(".parlay-away");
    const pickSelect = div.querySelector(".parlay-pick");
    const oddsInput = div.querySelector(".parlay-odds");

    homeSelect.addEventListener("change", async () => {
        const matches = await getMatchesForTeam(homeSelect.value);
        const opponents = matches.map(m => m.home === homeSelect.value ? m.away : m.home);
        awaySelect.innerHTML = opponents.map(t => `<option value="${t}">${t}</option>`).join("");
        if (opponents.length) awaySelect.value = opponents[0];
        updateParlayState();
    });

    if (teams.length) {
        homeSelect.value = teams[0];
        const matches = await getMatchesForTeam(teams[0]);
        const opponents = matches.map(m => m.home === teams[0] ? m.away : m.home);
        awaySelect.innerHTML = opponents.map(t => `<option value="${t}">${t}</option>`).join("");
        if (opponents.length) awaySelect.value = opponents[0];
    }

    div.querySelectorAll("select, input").forEach(el => {
        el.addEventListener("change", updateParlayState);
    });

    div.querySelector(".remove-btn").addEventListener("click", () => {
        div.remove();
        updateParlayState();
    });

    container.appendChild(div);
    updateParlayState();
}

function getValidSelections() {
    const rows = document.querySelectorAll(".selection-row");
    return Array.from(rows).map(row => ({
        home: row.querySelector(".parlay-home")?.value || "",
        away: row.querySelector(".parlay-away")?.value || "",
        pick: row.querySelector(".parlay-pick")?.value || "1",
        odds: parseFloat(row.querySelector(".parlay-odds")?.value) || null,
    })).filter(s => s.home && s.away);
}

function updateParlayState() {
    const valid = getValidSelections();
    const btn = document.getElementById("calculateParlayBtn");
    const empty = document.getElementById("parlayEmpty");
    const result = document.getElementById("parlayResult");

    if (valid.length >= 2) {
        btn.style.display = "inline-block";
        btn.disabled = false;
        empty.style.display = "none";
    } else if (valid.length > 0) {
        btn.style.display = "inline-block";
        btn.disabled = true;
        btn.textContent = valid.length === 1 ? "Agrega 1 selección más" : "Calcular Parlay";
        empty.style.display = "none";
    } else {
        btn.style.display = "none";
        empty.style.display = "block";
    }

    if (valid.length < 2) return;
    state.parlaySelections = valid;
}

async function calculateParlay() {
    const selections = getValidSelections();
    if (selections.length < 2) return;

    const btn = document.getElementById("calculateParlayBtn");
    btn.disabled = true;
    btn.textContent = "Calculando...";

    const data = await fetchAPI("/parlay/calculate", {
        method: "POST",
        body: JSON.stringify(selections),
    });

    btn.disabled = false;
    btn.textContent = "Calcular Parlay";

    if (!data) {
        document.getElementById("parlayResult").style.display = "block";
        document.getElementById("parlayResult").innerHTML = '<h3>Error al calcular</h3><p>Intenta de nuevo.</p>';
        return;
    }

    renderParlayResult(data);
}

function renderParlayResult(data) {
    const div = document.getElementById("parlayResult");
    div.style.display = "block";

    div.innerHTML = `
        <h3>Resultado del Parlay</h3>
        <div class="parlay-result-grid">
            <div class="parlay-result-item">
                <span>Probabilidad combinada</span>
                <span style="font-weight:700;font-size:1.1rem">${data.combined_probability}%</span>
            </div>
            <div class="parlay-result-item">
                <span>Valor Esperado (EV)</span>
                <span style="font-weight:700;color:${data.expected_value > 0 ? "var(--accent-green)" : "var(--accent-red)"}">
                    ${data.expected_value > 0 ? "+" : ""}${data.expected_value}%
                </span>
            </div>
            <div class="parlay-result-item">
                <span>Riesgo</span>
                <span class="risk-badge risk-${data.risk_level.toLowerCase().replace(" ", "-")}">${data.risk_level}</span>
            </div>
        </div>
        <div style="margin-top:1rem">
            <h4 style="margin-bottom:0.5rem;font-size:0.85rem;color:var(--text-secondary)">Selecciones:</h4>
            ${data.selections.map(s => `
                <div class="parlay-result-item">
                    <span>${s.match} → ${pickLabel(s.pick)}</span>
                    <span>${s.probability}%</span>
                </div>
            `).join("")}
        </div>
    `;
}

// ─────────── SAFEST PARLAYS ───────────

async function loadSafestParlays() {
    const container = document.getElementById("safestContainer");
    container.innerHTML = spinner("Calculando combinaciones seguras...");

    const size = parseInt(document.getElementById("safestSizeFilter").value);
    const data = await fetchAPI(`/parlay/safest?max_picks=${size}&min_prob=40`);

    if (!data?.suggestions?.length) {
        container.innerHTML = '<div class="empty-state">No se encontraron combinaciones con suficiente probabilidad.</div>';
        return;
    }

    const filtered = data.suggestions.filter(s => s.parlay_size === size);
    const display = filtered.length ? filtered : data.suggestions.slice(0, 10);

    container.innerHTML = display.map(s => {
        const probColor = s.combined_probability >= 40 ? "var(--accent-green)"
            : s.combined_probability >= 25 ? "var(--accent-yellow)"
            : "var(--accent-red)";
        return `
            <div class="suggestion-card">
                <span class="size-badge">${s.parlay_size} selección(es)</span>
                <ul>
                    ${s.selections.map(sel => `<li>${sel}</li>`).join("")}
                </ul>
                <div class="prob-display" style="color:${probColor}">
                    ${s.combined_probability}% probabilidad
                </div>
                <span class="risk-badge risk-${s.risk.toLowerCase().replace(" ", "-")}" style="margin-top:0.4rem;display:inline-block">
                    Riesgo: ${s.risk}
                </span>
            </div>
        `;
    }).join("");
}

// ─────────── FEATURE IMPORTANCE ───────────

async function loadFeatureImportance() {
    const container = document.getElementById("featureImportance");
    container.innerHTML = '<h3 style="margin-bottom:0.75rem">Importancia de Features (Random Forest)</h3>' + spinner();

    const data = await fetchAPI("/model/feature-importance");
    if (!data?.features?.length) {
        container.innerHTML += '<div class="empty-state">No disponible.</div>';
        return;
    }

    const maxImp = data.features[0].importance;
    container.innerHTML = '<h3 style="margin-bottom:0.85rem">Importancia de Features (Random Forest)</h3>' +
        data.features.map(f => `
            <div class="feature-bar-container">
                <div class="feature-bar-label">
                    <span>${f.feature}</span>
                    <span>${(f.importance * 100).toFixed(1)}%</span>
                </div>
                <div class="feature-bar">
                    <div class="feature-bar-fill" style="width:${(f.importance / maxImp) * 100}%"></div>
                </div>
            </div>
        `).join("");
}
