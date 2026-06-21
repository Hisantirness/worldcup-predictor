# 🏆 World Cup 2026 Parlay Predictor — Plan de Desarrollo

## Stack
- **Backend**: Python 3.13 + FastAPI + Uvicorn
- **Frontend**: HTML + CSS + Vanilla JS (SPA)
- **API**: football-data.org (free tier, 10 req/min)
- **ML**: BasicStats, Poisson, Elo, RandomForest → Ensemble con calibración Brier
- **Tests**: pytest + coverage
- **CI**: GitHub Actions (Ruff + pytest)
- **DB**: SQLite (caché)
- **Host**: Windows (dev) → Render/Railway (prod)

---

## 📋 Día 1 — Montar Frontend en Raíz (HOY)

### Objetivo
Que `localhost:8000` muestre la interfaz gráfica en vez de los docs de Swagger.

### Tareas
- [ ] Servir `frontend/index.html` como raíz (`/`)
- [ ] Mover Swagger a `/docs`
- [ ] Verificar que el frontend llame a `/api/v1/...` correctamente
- [ ] Probar todos los tabs: Dashboard, Parlay Builder, Picks Seguros
- [ ] Agregar **loading spinners** mientras carga la API
- [ ] Agregar **toast de error** si la API falla
- [ ] **Nav responsive** para mobile

### Criterios de éxito
- `localhost:8000` muestra el dashboard con partidos reales
- Los 3 tabs funcionan sin errores de consola
- Si la API tarda, se ve un spinner (no pantalla blanca)

---

## 📋 Día 2 — Frontend: Features + UX

### Objetivo
Mejorar la interfaz con más información y mejor experiencia.

### Tareas
- [ ] Tab de **predicciones detalladas**: mostrar cuotas 1X2, BTTS, O/U de cada modelo
- [ ] **Filtros**: por grupo, por fecha, por equipo
- [ ] Ordenar predicciones por confianza
- [ ] **Gráfico de barras** con probabilidades de cada resultado
- [ ] Tooltips/explicación de qué significa cada métrica
- [ ] Animaciones suaves al cambiar de tab

### Criterios de éxito
- Usuario puede filtrar partidos por grupo A-L
- Cada predicción muestra el detalle de los 4 modelos
- Las probabilidades se ven como barras visuales

---

## 📋 Día 3 — Backend: Nuevos Endpoints + Mercados

### Objetivo
Agregar más mercados de apuestas y datos de equipos.

### Tareas
- [ ] `GET /api/v1/team/{name}/stats` — estadísticas detalladas del equipo
- [ ] `GET /api/v1/head2head/{team_a}/{team_b}` — historial entre equipos
- [ ] Mercado **Under/Over 2.5** por modelo individual
- [ ] Mercado **BTTS** por modelo individual
- [ ] Mercado **Hándicap Asiático** (básico)
- [ ] Endpoint `GET /api/v1/markets/{match_id}` — todas las cuotas para un partido
- [ ] Cache en SQLite para reducir llamadas a football-data.org

### Criterios de éxito
- `GET /team/Argentina/stats` devuelve forma, goles promedio, BTTS%
- `GET /markets/1` devuelve 1X2, BTTS, O/U 2.5, Hándicap
- Todos los endpoints tienen tests

---

## 📋 Día 4 — Calibración + Tests

### Objetivo
Afinar los modelos con los 37 partidos reales y subir cobertura de tests.

### Tareas
- [ ] Ejecutar calibración con los 37 partidos terminados
- [ ] Evaluar Brier score de cada modelo
- [ ] Ajustar pesos del ensemble automáticamente
- [ ] Tests de integración: `GET /matches` con datos reales
- [ ] Tests de calibración con datos mock
- [ ] Tests de `api_client.py` (curl subprocess)
- [ ] Subir cobertura a >85%

### Criterios de éxito
- Los pesos del ensemble reflejan rendimiento real (no 20/30/25/25 fijo)
- Cobertura de tests ≥ 85%
- `test_calibration.py` existe con datos mock

---

## 📋 Día 5 — CI/CD + QA Final

### Objetivo
Pipeline de calidad automatizado y preparación para producción.

### Tareas
- [ ] GitHub Actions: Ruff lint + pytest + coverage report
- [ ] GitHub Actions: test en matrix 3.12/3.13 (ya existe)
- [ ] End-to-end test con Playwright (opcional)
- [ ] Revisar seguridad: CORS, headers, rate limiting
- [ ] `.env.example` con keys documentadas
- [ ] `README.md` con instrucciones de uso
- [ ] Revisar y limpiar código (remover archivos temporales)

### Criterios de éxito
- CI pasa en cada push
- README tiene setup, endpoints, ejemplos
- No hay archivos basura en el repo

---

## 📋 Día 6 — Despliegue a Producción

### Objetivo
Que el mundo pueda usar el predictor.

### Tareas
- [ ] Elegir plataforma: Render (free tier) o Railway
- [ ] Crear `Dockerfile` para backend
- [ ] Configurar variable de entorno `FOOTBALL_DATA_API_KEY`
- [ ] Desplegar backend
- [ ] Servir frontend desde FastAPI (ya integrado)
- [ ] Probar desde internet
- [ ] (Opcional) Dominio personalizado

### Criterios de éxito
- `https://worldcup-predictor.onrender.com` carga el dashboard
- API responde desde internet
- Funciona en celular

---

## 📋 Día 7+ — Features Avanzadas (Si hay tiempo)

### Objetivo
Funcionalidades extra que diferencian el producto.

### Tareas
- [ ] Predicción de **marcador exacto**
- [ ] **Simulador de grupo**: qué resultados necesita cada equipo para avanzar
- [ ] **Notificaciones** de partidos en vivo
- [ ] Historial de parlays guardados (localStorage)
- [ ] **Comparación** con cuotas reales de casas de apuesta
- [ ] Modo oscuro/claro toggle

---

## Estado Actual (Día 0 — Completado)

- ✅ Backend FastAPI con 4 modelos de predicción
- ✅ Ensemble con calibración Brier
- ✅ Calculadora de parlays (probabilidad combinada, EV, riesgo)
- ✅ API football-data.org integrada (72 partidos, 37 terminados)
- ✅ Root redirect a `/docs`
- ✅ 93 tests unitarios pasando
- ✅ GitHub repo: https://github.com/Hisantirness/worldcup-predictor
- ✅ `.env` con API key de football-data.org
- ✅ `.gitignore` protege `.env`

---

> **Nota**: Los días son estimados. Avanzamos al ritmo que sientas cómodo,
> probando y corrigiendo cada paso antes de seguir al siguiente.
