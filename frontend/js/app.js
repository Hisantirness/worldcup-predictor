const API_BASE = "http://localhost:8000/api/v1";

const state = {
    matches: [],
    predictions: [],
    selections: [],
    safest: [],
};

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    loadDashboard();
    initParlayBuilder();
});

function initNavigation() {
    document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");

            if (btn.dataset.tab === "safest") loadSafestParlays();
            if (btn.dataset.tab === "dashboard") loadDashboard();
        });
    });
}

async function fetchAPI(endpoint) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (err) {
        console.error(`API error (${endpoint}):`, err);
        return null;
    }
}

// ─────────── DASHBOARD ───────────

async function loadDashboard() {
    const container = document.getElementById("matchesContainer");
    container.innerHTML = '<div class="loading">Cargando partidos...</div>';

    const data = await fetchAPI("/predictions");
    if (!data || !data.predictions) {
        container.innerHTML = '<div class="loading">Error al cargar datos. Asegúrate de que el backend esté corriendo en localhost:8000.</div>';
        return;
    }

    state.predictions = data.predictions;
    renderMatches(data.predictions);

    document.getElementById("searchInput").addEventListener("input", applyFilters);
    document.getElementById("groupFilter").addEventListener("change", applyFilters);
}

function applyFilters() {
    const search = document.getElementById("searchInput").value.toLowerCase();
    const group = document.getElementById("groupFilter").value;

    let filtered = state.predictions;
    if (search) {
        filtered = filtered.filter(p =>
            p.home_team.toLowerCase().includes(search) ||
            p.away_team.toLowerCase().includes(search)
        );
    }
    if (group !== "all") {
        filtered = filtered.filter(p => p.group === group);
    }
    renderMatches(filtered);
}

function renderMatches(predictions) {
    const container = document.getElementById("matchesContainer");

    if (predictions.length === 0) {
        container.innerHTML = '<div class="loading">No se encontraron partidos.</div>';
        return;
    }

    container.innerHTML = predictions.map(p => `
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
            <div class="match-stats">
                <div class="stat-item">
                    <span class="stat-label">BTTS (ambos anotan)</span>
                    <span class="stat-value">${p.btts_probability}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Over 2.5 goles</span>
                    <span class="stat-value">${p.over_25_probability}%</span>
                </div>
            </div>
            <div class="safest-pick ${confidenceClass(p.confidence)}">
                <span>Pick más seguro: ${pickLabel(p.safest_pick)}</span>
                <span class="pick-badge">${p.confidence}% confianza</span>
            </div>
        </div>
    `).join("");
}

function pickLabel(pick) {
    return { "1": "1 (Local)", "X": "X (Empate)", "2": "2 (Visitante)" }[pick] || pick;
}

function confidenceClass(conf) {
    if (conf >= 55) return "high";
    if (conf >= 40) return "medium";
    return "low";
}

// ─────────── PARLAY BUILDER ───────────

function initParlayBuilder() {
    addSelectionRow();
    document.getElementById("addSelectionBtn").addEventListener("click", addSelectionRow);
}

function addSelectionRow() {
    const container = document.getElementById("parlaySelections");
    const idx = state.selections.length;

    const div = document.createElement("div");
    div.className = "selection-row";
    div.dataset.index = idx;

    div.innerHTML = `
        <div class="field">
            <label>Equipo Local</label>
            <input type="text" class="parlay-home" placeholder="Ej: Argentina">
        </div>
        <div class="field">
            <label>Equipo Visitante</label>
            <input type="text" class="parlay-away" placeholder="Ej: Brasil">
        </div>
        <div class="field">
            <label>Pick</label>
            <select class="parlay-pick">
                <option value="1">1 - Local</option>
                <option value="X">X - Empate</option>
                <option value="2">2 - Visitante</option>
            </select>
        </div>
        <div class="field">
            <label>Cuota (opcional)</label>
            <input type="number" class="parlay-odds" step="0.01" min="1.01" placeholder="Ej: 2.10">
        </div>
        <button class="remove-btn">✕</button>
    `;

    div.querySelector(".remove-btn").addEventListener("click", () => {
        div.remove();
        state.selections = state.selections.filter((_, i) => i !== idx);
        recalcParlay();
    });

    container.appendChild(div);

    state.selections.push({
        home: "",
        away: "",
        pick: "1",
        odds: null,
    });

    const inputs = div.querySelectorAll("input, select");
    inputs.forEach(input => {
        input.addEventListener("input", () => {
            const i = parseInt(div.dataset.index);
            state.selections[i] = {
                home: div.querySelector(".parlay-home").value,
                away: div.querySelector(".parlay-away").value,
                pick: div.querySelector(".parlay-pick").value,
                odds: parseFloat(div.querySelector(".parlay-odds").value) || null,
            };
        });
    });

    document.getElementById("parlayResult").style.display = "none";
}

async function recalcParlay() {
    const valid = state.selections.filter(s => s.home && s.away);
    if (valid.length === 0) {
        document.getElementById("parlayResult").style.display = "none";
        return;
    }

    const data = await fetchAPI("/parlay/calculate");
    if (data) {
        state.lastParlayResult = data;
        renderParlayResult(data);
    }
}

async function calculateParlay() {
    const valid = state.selections.filter(s => s.home && s.away);
    if (valid.length < 2) {
        alert("Agrega al menos 2 selecciones con equipos válidos.");
        return;
    }

    const data = await fetchAPI("/parlay/calculate");
    if (data) {
        renderParlayResult(data);
    }
}

function renderParlayResult(data) {
    const resultDiv = document.getElementById("parlayResult");
    resultDiv.style.display = "block";

    document.getElementById("parlayResultContent").innerHTML = `
        <div class="parlay-result-grid">
            <div class="parlay-result-item">
                <span>Probabilidad combinada</span>
                <span style="font-weight:700;font-size:1.1rem">${data.combined_probability}%</span>
            </div>
            <div class="parlay-result-item">
                <span>Valor Esperado (EV)</span>
                <span style="font-weight:700">${data.expected_value > 0 ? "+" : ""}${data.expected_value}%</span>
            </div>
            <div class="parlay-result-item">
                <span>Nivel de Riesgo</span>
                <span class="risk-badge risk-${data.risk_level.toLowerCase().replace(" ", "-")}">${data.risk_level}</span>
            </div>
        </div>
        <div style="margin-top:1rem">
            <h4 style="margin-bottom:0.5rem;font-size:0.9rem;color:var(--text-secondary)">Selecciones:</h4>
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
    container.innerHTML = '<div class="loading">Calculando combinaciones seguras...</div>';

    const data = await fetchAPI("/parlay/safest?max_picks=3&min_prob=45");
    if (!data || !data.suggestions) {
        container.innerHTML = '<div class="loading">No hay suficientes datos para sugerencias.</div>';
        return;
    }

    if (data.suggestions.length === 0) {
        container.innerHTML = '<div class="loading">No se encontraron picks con suficiente probabilidad.</div>';
        return;
    }

    container.innerHTML = data.suggestions.map((s, i) => `
        <div class="suggestion-card">
            <span class="size-badge">${s.parlay_size} selección(es)</span>
            <ul>
                ${s.selections.map(sel => `<li>${sel}</li>`).join("")}
            </ul>
            <div class="prob-display" style="color:${s.combined_probability >= 40 ? "var(--accent-green)" : s.combined_probability >= 25 ? "var(--accent-yellow)" : "var(--accent-red)"}">
                ${s.combined_probability}% probabilidad
            </div>
            <div class="risk-badge risk-${s.risk.toLowerCase().replace(" ", "-")}" style="margin-top:0.5rem">
                Riesgo: ${s.risk}
            </div>
        </div>
    `).join("");
}
