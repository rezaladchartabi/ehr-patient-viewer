from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import asyncio
from typing import Dict, List, Optional
from urllib.parse import urlparse
import time
import json
from collections import defaultdict
import os

# Configuration
FHIR_BASE_URL = "https://gel-landscapes-impaired-vitamin.trycloudflare.com/fhir"
CACHE_TTL = 300  # 5 minutes cache
RATE_LIMIT_REQUESTS = 100  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds

app = FastAPI(title="EHR FHIR Proxy", version="1.0.0")

# Allow CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory cache
cache: Dict[str, Dict] = {}
rate_limit_tracker: Dict[str, List[float]] = defaultdict(list)

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        # Clean old requests outside the window
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < self.window_seconds
        ]
        
        # Check if under limit
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(now)
            return True
        return False

rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW)

def get_cache_key(method: str, path: str, params: str) -> str:
    """Generate cache key from request details"""
    return f"{method}:{path}:{params}"

def is_cacheable(path: str) -> bool:
    """Check if the endpoint should be cached"""
    cacheable_endpoints = [
        "/Patient",
        "/Condition", 
        "/MedicationRequest",
        "/MedicationAdministration",
        "/Encounter",
        "/Observation",
        "/Procedure",
        "/Specimen"
    ]
    return any(path.startswith(endpoint) for endpoint in cacheable_endpoints)

async def fetch_from_fhir(path: str, params: Dict = None) -> Dict:
    """Fetch data from FHIR server"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{FHIR_BASE_URL}{path}"
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"FHIR server error: {response.text}"
            )
        
        return response.json()

def _cursor_allowed(cursor_url: str) -> bool:
    """Ensure the cursor URL points to the configured FHIR host/path to avoid SSRF."""
    try:
        target = urlparse(cursor_url)
        base = urlparse(FHIR_BASE_URL)
        if not target.netloc:
            return False
        # Allow both http/https as seen from server links; require same host and path prefix
        same_host = target.hostname == base.hostname
        return bool(same_host and target.path.startswith(base.path.rstrip('/')))
    except Exception:
        return False

@app.get("/paginate")
async def paginate(cursor: str):
    """Fetch a FHIR page via absolute 'next' link (cursor). Returns raw Bundle.

    The cursor must point to the configured FHIR host; otherwise 400 is returned.
    """
    if not _cursor_allowed(cursor):
        raise HTTPException(status_code=400, detail="Invalid cursor host")

    cache_key = get_cache_key("GET", "/paginate", cursor)
    if cache_key in cache:
        cached = cache[cache_key]
        if time.time() - cached["timestamp"] < CACHE_TTL:
            return cached["data"]

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(cursor)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"FHIR server error: {response.text}")
        data = response.json()

    cache[cache_key] = {"data": data, "timestamp": time.time()}
    return data

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    client_id = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_id):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )
    
    response = await call_next(request)
    return response

@app.get("/")
def read_root():
    return {
        "message": "EHR FHIR Proxy is running",
        "fhir_server": FHIR_BASE_URL,
        "cache_ttl": CACHE_TTL,
        "rate_limit": f"{RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds"
    }

@app.get("/Patient")
async def get_patients(
    _count: Optional[int] = 50,
    name: Optional[str] = None
):
    """Get patients from FHIR server with caching"""
    cache_key = get_cache_key("GET", "/Patient", f"count={_count}&name={name}")
    
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
    # Fetch from FHIR
    params = {"_count": _count}
    if name:
        params["name"] = name
    
    data = await fetch_from_fhir("/Patient", params)
    
    # Cache the result
    cache[cache_key] = {
        "data": data,
        "timestamp": time.time()
    }
    
    return data

@app.get("/Patient/by-ids")
async def get_patients_by_ids(ids: str):
    """Return a Bundle containing Patient resources for the given comma-separated IDs.

    Uses FHIR search parameter _id with comma-separated values in batches, merges entries,
    and returns as a single Bundle. Results are cached by the full ids list.
    """
    if not ids:
        return {"resourceType": "Bundle", "type": "searchset", "total": 0, "entry": []}

    # Normalize and cache
    id_list = [i.strip() for i in ids.split(',') if i.strip()]
    if not id_list:
        return {"resourceType": "Bundle", "type": "searchset", "total": 0, "entry": []}

    cache_key = get_cache_key("GET", "/Patient/by-ids", ",".join(sorted(id_list)))
    if cache_key in cache:
        cached = cache[cache_key]
        if time.time() - cached["timestamp"] < CACHE_TTL:
            return cached["data"]

    # Batch requests to avoid very long URLs; 20 per batch
    batch_size = 20
    entries: List[Dict] = []
    seen_ids = set()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(0, len(id_list), batch_size):
            batch = id_list[i:i+batch_size]
            params = {"_id": ",".join(batch), "_count": len(batch)}
            url = f"{FHIR_BASE_URL}/Patient"
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=f"FHIR server error: {resp.text}")
            bundle = resp.json()
            for e in (bundle.get("entry") or []):
                rid = e.get("resource", {}).get("id")
                if rid and rid not in seen_ids:
                    seen_ids.add(rid)
                    entries.append(e)

    result = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(entries),
        "entry": entries,
    }
    cache[cache_key] = {"data": result, "timestamp": time.time()}
    return result

@app.post("/prefetch")
async def prefetch_patients(payload: Dict):
    """Warm cache by pulling data for a list of patient IDs.

    Body: {"ids": ["patient-id", ...], "force": false}
    Returns counts of cached bundles by resource type.
    """
    ids = payload.get("ids") or []
    force = bool(payload.get("force", False))
    if not isinstance(ids, list) or not ids:
        return {"status": "ok", "message": "no ids provided", "counts": {}}

    resource_types = [
        ("/Condition", {"_count": 100}),
        ("/MedicationRequest", {"_count": 100}),
        ("/Encounter", {"_count": 100}),
        ("/MedicationAdministration", {"_count": 100}),
        ("/Observation", {"_count": 100}),
        ("/Procedure", {"_count": 100}),
        ("/Specimen", {"_count": 100}),
    ]

    counts: Dict[str, int] = {"Patient": 0}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Prefetch patients in batches using _id
        batch_size = 20
        total_entries = 0
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i+batch_size]
            params = {"_id": ",".join(batch), "_count": len(batch)}
            url = f"{FHIR_BASE_URL}/Patient"
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                bundle = resp.json()
                entries = len(bundle.get("entry") or [])
                total_entries += entries
                # cache Patient batch
                ckey = get_cache_key("GET", "/Patient", f"_id={params['_id']}&_count={params['_count']}")
                if force or ckey not in cache:
                    cache[ckey] = {"data": bundle, "timestamp": time.time()}
        counts["Patient"] = total_entries

        # Prefetch per-patient resources
        for pid in ids:
            for path, base_params in resource_types:
                params = dict(base_params)
                params["patient"] = f"Patient/{pid}"
                url = f"{FHIR_BASE_URL}{path}"
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    bundle = resp.json()
                    entries = len(bundle.get("entry") or [])
                    rname = path.strip("/")
                    counts[rname] = counts.get(rname, 0) + entries
                    ckey = get_cache_key("GET", path, f"patient={params['patient']}&count={params.get('_count')}")
                    if force or ckey not in cache:
                        cache[ckey] = {"data": bundle, "timestamp": time.time()}

    return {"status": "ok", "counts": counts}

@app.get("/Condition")
async def get_conditions(
    patient: Optional[str] = None,
    _count: Optional[int] = 100
):
    """Get conditions from FHIR server with caching"""
    cache_key = get_cache_key("GET", "/Condition", f"patient={patient}&count={_count}")
    
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    
    data = await fetch_from_fhir("/Condition", params)
    
    # Cache the result
    cache[cache_key] = {
        "data": data,
        "timestamp": time.time()
    }
    
    return data

@app.get("/MedicationRequest")
async def get_medication_requests(
    patient: Optional[str] = None,
    medication: Optional[str] = None,
    _count: Optional[int] = 100
):
    """Get medication requests from FHIR server with caching"""
    cache_key = get_cache_key("GET", "/MedicationRequest", f"patient={patient}&medication={medication}&count={_count}")
    
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    if medication:
        params["medication"] = medication
    
    data = await fetch_from_fhir("/MedicationRequest", params)
    
    # Cache the result
    cache[cache_key] = {
        "data": data,
        "timestamp": time.time()
    }
    
    return data

@app.get("/MedicationAdministration")
async def get_medication_administrations(
    patient: Optional[str] = None,
    _count: Optional[int] = 100
):
    """Get medication administrations from FHIR server with caching"""
    cache_key = get_cache_key("GET", "/MedicationAdministration", f"patient={patient}&count={_count}")
    
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    
    data = await fetch_from_fhir("/MedicationAdministration", params)
    
    # Cache the result
    cache[cache_key] = {
        "data": data,
        "timestamp": time.time()
    }
    
    return data

@app.get("/Encounter")
async def get_encounters(
    patient: Optional[str] = None,
    _count: Optional[int] = 100
):
    """Get encounters from FHIR server with caching"""
    cache_key = get_cache_key("GET", "/Encounter", f"patient={patient}&count={_count}")
    
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    
    data = await fetch_from_fhir("/Encounter", params)
    
    # Cache the result
    cache[cache_key] = {
        "data": data,
        "timestamp": time.time()
    }
    
    return data

@app.get("/Observation")
async def get_observations(
    patient: Optional[str] = None,
    code: Optional[str] = None,
    _count: Optional[int] = 100
):
    """Get observations from FHIR server with caching"""
    cache_key = get_cache_key("GET", "/Observation", f"patient={patient}&code={code}&count={_count}")
    
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    if code:
        params["code"] = code
    
    data = await fetch_from_fhir("/Observation", params)
    
    # Cache the result
    cache[cache_key] = {
        "data": data,
        "timestamp": time.time()
    }
    
    return data

@app.get("/Procedure")
async def get_procedures(
    patient: Optional[str] = None,
    _count: Optional[int] = 100
):
    """Get procedures from FHIR server with caching"""
    cache_key = get_cache_key("GET", "/Procedure", f"patient={patient}&count={_count}")
    
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    
    data = await fetch_from_fhir("/Procedure", params)
    
    # Cache the result
    cache[cache_key] = {
        "data": data,
        "timestamp": time.time()
    }
    
    return data

@app.get("/Specimen")
async def get_specimens(
    patient: Optional[str] = None,
    _count: Optional[int] = 100
):
    """Get specimens from FHIR server with caching"""
    cache_key = get_cache_key("GET", "/Specimen", f"patient={patient}&count={_count}")
    
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    
    data = await fetch_from_fhir("/Specimen", params)
    
    # Cache the result
    cache[cache_key] = {
        "data": data,
        "timestamp": time.time()
    }
    
    return data

@app.get("/cache/status")
def get_cache_status():
    """Get cache status and statistics"""
    now = time.time()
    active_cache_entries = 0
    expired_cache_entries = 0
    
    for key, value in cache.items():
        if now - value["timestamp"] < CACHE_TTL:
            active_cache_entries += 1
        else:
            expired_cache_entries += 1
    
    return {
        "total_cache_entries": len(cache),
        "active_cache_entries": active_cache_entries,
        "expired_cache_entries": expired_cache_entries,
        "cache_ttl_seconds": CACHE_TTL,
        "rate_limit_requests": RATE_LIMIT_REQUESTS,
        "rate_limit_window_seconds": RATE_LIMIT_WINDOW
    }

@app.post("/cache/clear")
def clear_cache():
    """Clear all cached data"""
    global cache
    cache.clear()
    return {"message": "Cache cleared successfully"}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )
