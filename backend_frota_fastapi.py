from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os, requests, traceback
from time import time
from dotenv import load_dotenv

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

# =========================
# FALLBACK TEMPORÁRIO
# =========================
FALLBACK_DATA = [
    {
        "unidade": "ITAITINGA",
        "placa": "JUX7E77",
        "status": "ROTA",
        "motorista": "SAMUEL SILVA DE LIMA",
        "localizacao": "RUA R - ITAITINGA",
        "rota": "19",
        "rom": "8528",
        "prev_retorno": None
    },
    {
        "unidade": "PICOS",
        "placa": "HYU3B28",
        "status": "ROTA",
        "motorista": "—",
        "localizacao": "BR-230 - PICOS",
        "rota": None,
        "rom": None,
        "prev_retorno": None
    },
    {
        "unidade": "IMPERATRIZ",
        "placa": "SBC9D25",
        "status": "ROTA",
        "motorista": "WELISSON SILVA FEITOSA",
        "localizacao": "BR-010 - IMPERATRIZ",
        "rota": "43",
        "rom": "7182",
        "prev_retorno": "2026-01-06"
    },
    {
        "unidade": "BELÉM",
        "placa": "SBD5B25",
        "status": "PATIO",
        "motorista": "FAGNER AUGUSTO OLIVEIRA",
        "localizacao": "BR-316 - CASTANHAL",
        "rota": "38",
        "rom": "1183",
        "prev_retorno": None
    }
]

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
        return _cache["data"]

    try:
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

    except Exception as e:
        print("⚠️ FALLBACK ATIVADO")
        traceback.print_exc()

        return {
            "fallback": True,
            "data": FALLBACK_DATA
        }
