# How to Run the Walking-Tour Guide (Efrat's part)

This covers **three** runnable things in the repo:

| What | File | Needs an OpenAI key? | Best place to run |
|---|---|---|---|
| Data tools only | `scripts/run_tools.py` | ❌ no | Local **or** Colab |
| Full agent (tools + LLM) | `scripts/run_agent.py` | ✅ yes | Local **or** Colab |
| **The Streamlit app + map** | `app.py` | ✅ yes (or fake mode) | **Local** (Colab needs a tunnel) |

> **Short version:** the *scripts* run anywhere. The *Streamlit app* is a local web
> server, so **running it locally is the smoother experience**. It still works in
> Colab, but only through a public tunnel (instructions below).

---

## A) Run locally — recommended for the app

From a clean clone of the repo:

```bash
# 1. create + activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows (PowerShell)

# 2. install everything (now includes streamlit, folium, streamlit-folium)
pip install -r requirements.txt

# 3. add your OpenAI key
cp .env.example .env               # copy .env.example .env   on Windows
#   then edit .env and set:  OPENAI_API_KEY=sk-...your real key...
```

### Launch the app

```bash
streamlit run app.py
```

It opens at `http://localhost:8501`. Type an address (e.g. *Allenby 29, Tel Aviv*),
tap a few interests, press **Build my tour**, and the itinerary + route map appear.

### Build the whole UI with **no key / no agent** (demo / dev mode)

Useful before integration, or as a live-demo fallback if the WiFi dies. It serves a
built-in sample tour so every screen works:

```bash
USE_FAKE_AGENT=1 streamlit run app.py          # macOS / Linux
set USE_FAKE_AGENT=1 && streamlit run app.py    # Windows cmd
$env:USE_FAKE_AGENT=1; streamlit run app.py     # Windows PowerShell
```

### The two helper scripts (no app needed)

```bash
python scripts/run_tools.py     # data tools only — no key. Edit ADDRESS/INTERESTS inside.
python scripts/run_agent.py     # full agent — needs the key. Edit ADDRESS/INTERESTS/NOTE inside.
```

### Run the tests

```bash
# fast, offline — no key, no network
pytest tests/test_app_unit.py tests/test_tools_unit.py -v

# everything, including live OpenStreetMap tests (needs internet)
pytest -v
```

---

## B) Run in Google Colab

Open **`Walking_Tour_Colab.ipynb`** in Colab (Upload, or *File → Open notebook → GitHub*)
and run the cells top to bottom. Here's what each part does and why.

### 1. Get the code into Colab
Either upload `DS-TravelAi-main.zip` with the file picker (the first cell does this and
unzips it), or `git clone` your repo. Then `%cd DS-TravelAi-main`.

### 2. Install dependencies
```python
!pip install -r requirements.txt -q
```

### 3. Add your OpenAI key (only for the agent/app, not the tools)
Use Colab **Secrets** (the 🔑 in the left sidebar) — add a secret named `OPENAI_API_KEY`,
then:
```python
import os
from google.colab import userdata
os.environ["OPENAI_API_KEY"] = userdata.get("OPENAI_API_KEY")
```

### 4a. Tools + agent in Colab — **no tunnel needed**
These just print, so they run like any Python:
```python
# tools only (no key)
from tools import get_nearby_places, order_walking_route
places = get_nearby_places("Allenby 29, Tel Aviv", ["cafe", "architecture"])
for p in order_walking_route(places):
    print(p.name, "|", p.category)

# full agent (needs the key set in step 3, BEFORE this import)
import json
from agent.agent import run_agent
raw = run_agent("Allenby 29, Tel Aviv", ["architecture", "cafe", "art"])
print(json.loads(raw) if isinstance(raw, str) else raw)
```

### 4b. The Streamlit **app** in Colab — needs a public tunnel
Colab can't show a Streamlit server inline (it runs on `localhost` inside Google's VM),
so we expose it with **cloudflared** — no signup, no password:

```python
import subprocess, time, re, pathlib

# one-time: download the cloudflared binary
!wget -q -O cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x cloudflared

# start the app in the background
subprocess.Popen(["streamlit", "run", "app.py",
                   "--server.port", "8501", "--server.headless", "true"],
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(8)

# open a public tunnel and print its URL
log = open("cf.log", "w")
subprocess.Popen(["./cloudflared", "tunnel", "--url", "http://localhost:8501"],
                 stdout=log, stderr=log)
url = None
for _ in range(30):
    time.sleep(1)
    m = re.search(r"https://[-\w]+\.trycloudflare\.com", pathlib.Path("cf.log").read_text())
    if m:
        url = m.group(0); break
print("👉 Open your app here:", url or "not ready yet — re-run this cell")
```

Click the printed `…trycloudflare.com` link to use the full app (map included).

> **Alternative tunnel (localtunnel):** `!npm install -g localtunnel` then
> `!streamlit run app.py &>/dev/null & npx localtunnel --port 8501`.
> localtunnel asks for a password — it's the VM's IP from
> `!wget -q -O - https://ipv4.icanhazip.com`.

### Colab caveats (worth knowing for the demo)
- Free Colab VMs idle out after a while; the tunnel URL dies with the VM. For the graded
  **live demo, run locally** — it's faster and has nothing extra to break.
- Use Colab only if you can't install Python locally, or to share a quick link with a teammate.
- Keep your key in Colab **Secrets**, never pasted into a cell you might commit.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: streamlit` | `pip install -r requirements.txt` (it's now listed there) |
| Map doesn't show, pins do | folium missing — the app auto-falls back to `st.map`; install `streamlit-folium` to get the path |
| "tour-building service is unavailable" | bad/empty `OPENAI_API_KEY`, or no billing on the key |
| "No matching places nearby" | the address is too quiet — try a more central one or add interests |
| Want to demo with no key | `USE_FAKE_AGENT=1 streamlit run app.py` |
| Colab link won't open | the VM idled out — re-run the tunnel cell, or run locally |
