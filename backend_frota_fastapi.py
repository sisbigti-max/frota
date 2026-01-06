from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
from dotenv import load_dotenv
from time import time
import traceback

# =====================================================
# CONFIGURAÇÃO INICIAL
# =====================================================

load_dotenv()

ZUQ_TOKEN = os.getenv("ZUQ_TOKEN")
ZUQ_BASE = "https://app.zuq.com.br/api"

HEADERS = {
    "Authorization": f"Bearer {ZUQ_TOKEN}",
    "Accept": "application/json"
}

CACHE_TTL = 30  # segundos
_cache = {"ts": 0, "data": []}

# =====================================================
# APP FASTAPI (CRIE APENAS UMA VEZ)
# =====================================================

app = FastAPI(title="Ipê Química • API Frota")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # libera web
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# FUNÇÕES DE INTEGRAÇÃO ZUQ
# =====================================================

def fetch_vehicles():
    resp = requests.get(
        f"{ZUQ_BASE}/vehicles/v2/list?page=1&size=500",
        headers=HEADERS,
        timeout=20
    )
    resp.raise_for_status()
    return resp.json().get("data", [])

def fetch_realtime():
    resp = requests.get(
        f"{ZUQ_BASE}/realtime/vehicles",
        headers=HEADERS,
        timeout=20
    )
    resp.raise_for_status()
    return resp.json().get("data", [])

# =====================================================
# ENDPOINT PRINCIPAL (BLINDADO)
# =====================================================

@app.get("/api/frota")
def frota():
    global _cache

    try:
        now = time()

        # cache
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

    except Exception as e:
        print("❌ ERRO NO /api/frota")
        traceback.print_exc()
        return {
            "error": True,
            "message": "Erro interno ao carregar frota",
            "detail": str(e)
        }

# =====================================================
# HEALTHCHECK (IMPORTANTE)
# =====================================================

@app.get("/")
def health():
    return {"status": "ok"}
