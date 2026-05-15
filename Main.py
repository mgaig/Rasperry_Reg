import time
import json
from datetime import datetime, date
from gpiozero import OutputDevice

# -----------------------------
# CONFIGURACIÓN
# -----------------------------

VALVES = {
    1: OutputDevice(17),
    2: OutputDevice(27),
    3: OutputDevice(22),
    4: OutputDevice(23)
}

CONFIG_FILE = "Config.json"
STATE_FILE = "state.json"

# -----------------------------
# CARGA CONFIG
# -----------------------------

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"last_run": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -----------------------------
# LÓGICA DE RIEGO
# -----------------------------

def run_irrigation(config):
    duration = config["duration_seconds"]

    print("🚿 Iniciando riego...")

    for valve_id in sorted(VALVES.keys()):
        print(f"Abriendo válvula {valve_id}")

        valve = VALVES[valve_id]
        valve.on()

        time.sleep(duration)

        valve.off()
        print(f"Cerrando válvula {valve_id}")

        time.sleep(2)  # pausa entre zonas

    print("✅ Riego completado")

# -----------------------------
# MAIN LOOP
# -----------------------------

def main():
    config = load_config()
    state = load_state()

    while True:
        now = datetime.now().date().isoformat()

        if state["last_run"] != now:
            run_irrigation(config)

            state["last_run"] = now
            save_state(state)

        else:
            print("⏳ Ya se ha regado hoy")

        time.sleep(60)  # chequeo cada minuto


if __name__ == "__main__":
    main()
