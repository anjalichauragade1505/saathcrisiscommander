# SAATH Crisis Commander — v1

An agentic emergency-response coordination simulation for Nagpur. Simulates flood
and earthquake events across 8 real Nagpur localities (including the Wadi / Katol
Road area where RCOEM / Ramdeobaba University sits), runs a multi-agent pipeline
(Situation → Resource → Routing → Response Planner), requires human approval
before any resource commitment, and uses one real LLM call (the **Inference
Agent**) to predict secondary needs — e.g. an evacuation into a zone triggering
a predicted food-shortage notification to a different stakeholder (District Food
Officer) who was never told directly by the Commander.

Everything else in the pipeline is deliberately rule-based and explainable —
see `backend/app/agents/` for exactly which agent is which.

---

## 1. Project structure

```
saath-crisis-commander/
├── backend/              FastAPI + SQLite + agent pipeline
│   ├── app/
│   │   ├── agents/       situation, resource, routing, inference (LLM), planner, notifier
│   │   ├── models.py     SQLAlchemy models
│   │   ├── routes.py     all API endpoints
│   │   ├── seed_data.py  8 real Nagpur zones, roads, resources
│   │   └── main.py       app entry point
│   ├── requirements.txt
│   └── .env.example
└── frontend/             React + Vite + Tailwind command-center UI
    ├── src/
    │   ├── components/   map, panels, event injection modal, role views
    │   └── App.jsx
    └── .env.example
```

---

## 2. Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- An **Anthropic API key** (for the one real AI call — the Inference Agent).
  Get one at https://console.anthropic.com/ — without it, the Inference Agent
  automatically falls back to a rule-based estimate, so the app still runs
  fully without a key, just without the real reasoning step.

---

## 3. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# open .env and paste your key:
#   ANTHROPIC_API_KEY=sk-ant-...
#   MODEL_NAME=claude-sonnet-5

uvicorn app.main:app --reload --port 8000
```

The API is now running at `http://localhost:8000`. Interactive API docs (handy
for testing endpoints directly, and a nice thing to show in an interview) are
at `http://localhost:8000/docs`. The database (`saath.db`) and all 8 Nagpur
zones are created and seeded automatically on first startup.

---

## 4. Frontend setup

Open a **second terminal**:

```bash
cd frontend
npm install

cp .env.example .env
# default already points to http://localhost:8000, only change if you
# deploy the backend elsewhere

npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 5. Running the demo script

This walks through the exact scenario the system is designed to prove —
memorize this sequence for your interview demo:

1. You start on the **Incident Commander** view. All 8 zones show LOW severity.
2. Click **⚡ Inject New Event** → choose **Flood** → set rainfall to **60** mm/hr → Simulate Event.
3. Watch the map: **Wadi – Katol Road (RBU Campus Area)** turns CRITICAL
   (this is deliberately the zone that reaches CRITICAL first — it has the
   highest flood-risk score in the seed data, modeling its low-lying,
   poor-drainage geography near Ambazari).
4. Check **Pending Approval** — you'll see a rescue-team + ambulance dispatch
   to that zone, flagged "Evacuation-scale action".
5. Click **Approve** on the rescue-team dispatch.
6. Watch what happens: the **Inference Agent** fires (a real Claude API call
   if you added a key, otherwise the rule-based fallback — both are logged
   and both are visible in the response). It predicts a food-kit shortage in
   that zone and you'll see the reasoning in a toast plus in the Incident Feed.
7. Switch the role toggle (top bar) to **District Food Officer** — you'll see
   the notification with the AI's reasoning and confidence score, that the
   Commander never directly sent. Approve the relief dispatch.
8. Switch role back to Commander, then **Inject New Event → Road blocked →
   Bridge-2**. Watch the Routing Agent recalculate and any affected pending
   actions get flagged.
9. Switch to **Field Reporter**, select the Wadi/RBU zone. Inject a
   **Communication failure** event on that zone (from the Commander view),
   then go back to Field Reporter and try "Report Situation" — it queues
   locally instead of failing outright. Inject **Connectivity restored** and
   watch it auto-sync with a logged delay.

That's the full loop: simulate → multi-agent reasoning → human approval →
AI-inferred cross-stakeholder need → second human approval → dynamic
replanning → offline-first field resilience.

---

## 6. What's real AI vs rule-based (say this plainly in interviews)

| Step | Type |
|---|---|
| Situation Agent (severity scoring) | Rule-based formula |
| Resource Agent (allocation ranking) | Rule-based scoring |
| Routing Agent (path validity) | Rule-based BFS over road graph |
| **Inference Agent (secondary need prediction)** | **Real Claude API call**, with a rule-based fallback if the call fails/times out |
| Response Planner / Notifier | Rule-based aggregation and routing table |

This split is intentional, not a limitation — see the project blueprint doc
for the full reasoning behind it.

---

## 7. Known v1 limitations (say these are "phase 2", not oversights)

- No authentication — role is a UI toggle, not a login system (no multi-tenant
  data to protect in a single-user simulation).
- No real map/GIS — zones are simulated on an 800x600 grid, not real lat/lng.
- No WebSockets — frontend polls every 2s; would swap to WebSockets first if
  scaling to real concurrent users.
- No mobile app — the Field Reporter role runs inside the same web app for v1.
- Risk forecast is a synthetic curve derived from current severity, not a
  real time-series/weather model.

---

## 8. Troubleshooting

- **Frontend shows "Cannot reach backend"** — make sure `uvicorn` is running
  on port 8000 and `frontend/.env`'s `VITE_API_URL` matches.
- **CORS errors in browser console** — confirm you didn't change the backend
  port without updating `VITE_API_URL`.
- **Inference Agent always says "fallback used"** — check `backend/.env` has
  a valid `ANTHROPIC_API_KEY` and restart `uvicorn` after editing it.
- **Want a clean slate** — click "Reset Simulation" in the Commander view, or
  stop the backend and delete `backend/saath.db`.
