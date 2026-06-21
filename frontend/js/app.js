const API_BASE = "http://localhost:8000/api/v1";

const state = {
    predictions: [],
    parlaySelections: [],
    connected: false,
};

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    loadDashboard();
    initParlayBuilder();
    loadFeatureImportance();

    document.getElementById("refreshBtn").addEventListener("click", loadDashboard);
    document.getElementById("safestSizeFilter").addEventListener("change", loadSafestParlays);
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
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        state.connected = true;
        document.getElementById("connectionBanner").style.display = "none";
        return await res.json();
    } catch (err) {
        console.error(`API error (${endpoint}):`, err);
        if (!state.connected) {
            document.getElementById("connectionBanner").style.display = "flex";
        }
        return null;
    }
}

// ─────────── NAVIGATION ───────────

function initNavigation() {
    document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".nav-btn, .tab-content").forEach(el => el.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
            const tab = btn.dataset.tab;
            if (tab === "safest") loadSafestParlays();
            if (tab === "models") loadFeatureImportance();
            if (tab === "dashboard") loadDashboard();
        });
    });
}

// ─────────── DASHBOARD ───────────

async function loadDashboard() {
    const container = document.getElementById("matchesContainer");
    container.innerHTML = '<div class="loading">⟳ Cargando partidos...</div>';

    const data = await fetchAPI("/predictions");
    if (!data?.predictions) {
        container.innerHTML = '<div class="loading">Error al cargar datos. Verifica que el backend esté corriendo en localhost:8000.</div>';
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
    if (group !== "all") filtered = filtered.filter(p => p.group === group);
    renderMatches(filtered);
}

function renderMatches(predictions) {
    const container = document.getElementById("matchesContainer");
    if (!predictions.length) {
        container.innerHTML = '<div class="empty-state">No se encontraron partidos.</div>';
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
                    <span class="stat-label">BTTS</span>
                    <span class="stat-value">${p.btts_probability}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Over 2.5</span>
                    <span class="stat-value">${p.over_25_probability}%</span>
                </div>
            </div>
            <div class="safest-pick ${confidenceClass(p.confidence)}">
                <span>Pick: ${pickLabel(p.safest_pick)}</span>
                <span class="pick-badge">${p.confidence}%</span>
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
    container.innerHTML = '<div class="loading">Calculando combinaciones seguras...</div>';

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
    container.innerHTML = '<h3 style="margin-bottom:0.75rem">Importancia de Features (Random Forest)</h3><div class="loading">Cargando...</div>';

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
