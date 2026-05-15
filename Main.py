from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from gpiozero import Device, OutputDevice
from gpiozero.pins.lgpio import LGPIOFactory
import json
import time
import threading
from datetime import datetime

# =====================================================
# GPIO SETUP (IMPORTANTE para Raspberry Pi OS moderno)
# =====================================================
Device.pin_factory = LGPIOFactory()

# =====================================================
# FASTAPI
# =====================================================
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# =====================================================
# GPIO PINS (4 válvulas)
# =====================================================
VALVES = {
    1: OutputDevice(17),
    2: OutputDevice(27),
    3: OutputDevice(22),
    4: OutputDevice(23)
}

# =====================================================
# CONFIG / STATE
# =====================================================
CONFIG_FILE = "config.json"

state = {
    "running": False,
    "last_run": None
}

# =====================================================
# LOAD CONFIG
# =====================================================
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
def run_irrigation(duration):
    state["running"] = True
    print("🚿 Starting irrigation...")

    # seguridad: todo OFF antes de empezar
    for v in VALVES.values():
        v.off()

    for i in range(1, 5):
        print(f"Valve {i} ON")
        VALVES[i].on()
        time.sleep(duration)
        VALVES[i].off()
        print(f"Valve {i} OFF")

        time.sleep(2)  # pausa entre zonas

    state["running"] = False
    state["last_run"] = datetime.now().isoformat()

    print("✅ Irrigation finished")

# =====================================================
# BACKGROUND SCHEDULER (1 vez al día)
# =====================================================
def scheduler():
    while True:
        config = load_config()
        now = datetime.now().date().isoformat()

        if state["last_run"] != now:
            run_irrigation(config["duration"])

        time.sleep(60)  # check cada minuto


# =====================================================
# START BACKGROUND THREAD
# =====================================================
threading.Thread(target=scheduler, daemon=True).start()

# =====================================================
# WEB UI
# =====================================================
@app.get("/", response_class=HTMLResponse)
def root():
    return "<h2>Irrigation system OK → /ui</h2>"


@app.get("/ui", response_class=HTMLResponse)
def ui(request: Request):
    return templates.TemplateResponse("ui.html", {"request": request})


# =====================================================
# API
# =====================================================
@app.get("/status")
def get_status():
    return state


@app.post("/set_duration")
def set_duration(data: dict):
    config = load_config()
    config["duration"] = data["duration"]
    save_config(config)
    return {"ok": True, "duration": config["duration"]}


@app.post("/start")
def start_manual():
    config = load_config()

    thread = threading.Thread(
        target=run_irrigation,
        args=(config["duration"],),
        daemon=True
    )
    thread.start()

    return {"ok": True, "message": "irrigation started"}