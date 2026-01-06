from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import traceback

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from time import time

load_dotenv()

ZUQ_TOKEN = os.getenv("ZUQ_TOKEN")
ZUQ_BASE = "https://app.zuq.com.br/api"

HEADERS = {
    "Authorization": f"Bearer {ZUQ_TOKEN}",
    "Accept": "application/json"
}

CACHE_TTL = 30  # segundos
_cache = {"ts": 0, "data": []}

app = FastAPI(title="Ipê Química • API Frota")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def fetch_vehicles():
    r = requests.get(f"{ZUQ_BASE}/vehicles/v2/list?page=1&size=500", headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json().get("data", [])

def fetch_realtime():
    r = requests.get(f"{ZUQ_BASE}/realtime/vehicles", headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json().get("data", [])

@app.get("/api/frota")
def frota():
    global _cache
    now = time()

    if now - _cache["ts"] < CACHE_TTL:
        return _cache["data"]

    vehicles = fetch_vehicles()
    realtime = fetch_realtime()

    rt_map = {v.get("vehicle_id"): v for v in realtime}

    result = []
    for v in vehicles:
        rt = rt_map.get(v.get("id"), {})
        status = "AG_INFO"
        if rt.get("ignition") is True:
            status = "ROTA"
        elif rt.get("ignition") is False:
            status = "PATIO"

        result.append({
            "unidade": v.get("group_name"),
            "placa": v.get("plate"),
            "status": status,
            "motorista": v.get("driver_name"),
            "localizacao": rt.get("address"),
            "rota": v.get("route_code"),
            "rom": v.get("last_rom"),
            "prev_retorno": v.get("expected_return"),
        })

    _cache = {"ts": now, "data": result}
    return result
