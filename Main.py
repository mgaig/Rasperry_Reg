from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from gpiozero import OutputDevice
import json
import time
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ---------------- GPIO ----------------
VALVES = {
    1: OutputDevice(17),
    2: OutputDevice(27),
    3: OutputDevice(22),
    4: OutputDevice(23)
}

# ---------------- CONFIG ----------------
CONFIG_FILE = "config.json"
state = {"running": False}


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def run_irrigation(duration):
    state["running"] = True

    for v in VALVES.values():
        v.off()

    for i in range(1, 5):
        print(f"Valve {i} ON")
        VALVES[i].on()
        time.sleep(duration)
        VALVES[i].off()

    state["running"] = False


# ---------------- WEB ----------------
@app.get("/", response_class=HTMLResponse)
def root():
    return "<h2>Riego OK. Ve a /ui</h2>"


@app.get("/ui", response_class=HTMLResponse)
def ui(request: Request):
    return templates.TemplateResponse("ui.html", {"request": request})


@app.get("/status")
def status():
    return state


@app.post("/set_duration")
def set_duration(data: dict):
    config = load_config()
    config["duration"] = data["duration"]

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

    return {"ok": True, "duration": data["duration"]}


@app.post("/start")
def start():
    config = load_config()
    duration = config.get("duration", 10)

    run_irrigation(duration)
    return {"ok": True, "message": "Irrigation completed"}