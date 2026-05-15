from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from gpiozero import OutputDevice
import json
import time
import threading
from datetime import datetime

# =====================================================
# FASTAPI
# =====================================================
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# =====================================================
# GPIO (SIN lgpio explícito → automático y estable)
# =====================================================
VALVES = {
    1: OutputDevice(17),
    2: OutputDevice(27),
    3: OutputDevice(22),
    4: OutputDevice(23)
}

# =====================================================
# CONFIG
# =====================================================
CONFIG_FILE = "config.json"

state = {
    "running": False,
    "last_run": None
}


def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"duration": 30}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

# =====================================================
# IRRIGATION LOGIC
# =====================================================
def run_irrigation(duration: int):
    print("🚿 Starting irrigation")
    state["running"] = True

    # seguridad: todo OFF
    for v in VALVES.values():
        v.off()

    for i in range(1, 5):
        print(f"Valve {i} ON")
        VALVES[i].on()

        time.sleep(duration)

        VALVES[i].off()
        print(f"Valve {i} OFF")

        time.sleep(2)

    state["running"] = False
    state["last_run"] = datetime.now().isoformat()

    print("✅ Finished irrigation")

# =====================================================
# SCHEDULER (1 vez al día)
# =====================================================
def scheduler():
    while True:
        config = load_config()
        today = datetime.now().date().isoformat()

        if state["last_run"] != today:
            run_irrigation(config["duration"])

        time.sleep(60)


threading.Thread(target=scheduler, daemon=True).start()

# =====================================================
# WEB
# =====================================================
@app.get("/", response_class=HTMLResponse)
def root():
    return "<h2>Riego OK → /ui</h2>"


@app.get("/ui", response_class=HTMLResponse)
def ui(request: Request):
    return templates.TemplateResponse("ui.html", {"request": request})

# =====================================================
# API
# =====================================================
@app.get("/status")
def status():
    return state


@app.post("/start")
def start_manual():
    config = load_config()

    t = threading.Thread(
        target=run_irrigation,
        args=(config["duration"],),
        daemon=True
    )
    t.start()

    return {"ok": True}


@app.post("/set_duration")
def set_duration(data: dict):
    config = load_config()
    config["duration"] = data["duration"]
    save_config(config)

    return {"ok": True, "duration": config["duration"]}