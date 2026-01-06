from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from dotenv import load_dotenv
from time import time

load_dotenv()

app = FastAPI(title="Ipê Química • API Frota")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ZUQ_TOKEN = os.getenv("ZUQ_TOKEN")
ZUQ_BASE = "https://app.zuq.com.br/api"

HEADERS = {
    "Authorization": f"Bearer {ZUQ_TOKEN}",
    "Accept": "application/json"
}

CACHE_TTL = 30
_cache = {"ts": 0, "data": []}


def fetch_vehicles():
    r = requests.get(
        f"{ZUQ_BASE}/vehicles/v2/list?page=1&size=500",
        headers=HEADERS,
        timeout=20
    )
    r.raise_for_status()
    return r.json().get("data", [])


def fetch_realtime():
    r = requests.get(
        f"{ZUQ_BASE}/realtime/vehicles",
        headers=HEADERS,
        timeout=20
    )
    r.raise_for_status()
    return r.json().get("data", [])


@app.get("/api/frota")
def frota():
    global _cache
    now = time()

    if now - _cache["ts"] < CACHE_TTL:
        return _cache["data"]  # 👈 array direto

    vehicles = fetch_vehicles()
    realtime = fetch_realtime()

    rt_map = {str(v.get("vehicle_id")): v for v in realtime}

    resultado = []

    for v in vehicles:
        rt = rt_map.get(str(v.get("id")), {})

        if rt.get("ignition") is True:
            status = "ROTA"
        elif rt.get("ignition") is False:
            status = "PATIO"
        else:
            status = "AG_INFO"

        resultado.append({
            "unidade": v.get("group_name") or "---",
            "placa": v.get("plate") or "---",
            "status": status,
            "zuq_entrada": v.get("entry_time") or "---",
            "zuq_saida": v.get("exit_time") or "---",
            "manut_tipo": "---",
            "gfs_entrada": "---",
            "gfs_saida": "---",
            "supersoft": v.get("status") or "---",
            "motorista": v.get("driver_name") or "---",
            "localizacao": rt.get("address") or "---",
            "rota": v.get("route_code") or "---",
            "rom": v.get("last_rom") or "---",
            "prev_retorno": v.get("expected_return") or "---"
        })

    _cache = {"ts": now, "data": resultado}
    return resultado  # 👈 ARRAY PURO
