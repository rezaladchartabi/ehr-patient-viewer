from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from urllib.parse import urlencode
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
app.add_middleware(GZipMiddleware, minimum_size=500)

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
    """Generate cache key from request details (already-stringified params)."""
    return f"{method}:{path}:{params}"

def build_cache_key(method: str, path: str, params_dict: Dict[str, Any]) -> str:
    """Normalize params (sorted, urlencoded) for consistent cache keys."""
    items = [(k, v) for k, v in params_dict.items() if v is not None and v != ""]
    items.sort(key=lambda x: x[0])
    query = urlencode(items, doseq=True)
    return get_cache_key(method, path, query)

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

# Reusable HTTP client
_client: httpx.AsyncClient | None = None

@app.on_event("startup")
async def _startup_client():
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)

@app.on_event("shutdown")
async def _shutdown_client():
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None

async def fetch_from_fhir(path: str, params: Dict = None) -> Dict:
    """Fetch data from FHIR server with shared client"""
    if _client is None:
        # fallback safety
        client = httpx.AsyncClient(timeout=30.0)
    else:
        client = _client
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

async def _fetch_all_pages(path: str, params: Dict[str, Any]) -> List[Dict]:
    """Fetch first page and follow link[next] until exhausted. Returns entry list."""
    # First page
    first = await fetch_from_fhir(path, params)
    entries: List[Dict] = list(first.get("entry") or [])
    links = first.get("link") or []
    next_link = next((l.get("url") for l in links if l.get("relation") == "next"), None)
    # Follow next links using shared client (direct GET)
    if next_link:
        async with httpx.AsyncClient(timeout=30.0) as client:
            cursor = next_link
            while cursor:
                resp = await client.get(cursor)
                if resp.status_code != 200:
                    break
                page = resp.json()
                entries.extend(page.get("entry") or [])
                links = page.get("link") or []
                cursor = next((l.get("url") for l in links if l.get("relation") == "next"), None)
    return entries

def _map_med_req(res: Dict[str, Any]) -> Dict[str, Any]:
    c = (res.get("medicationCodeableConcept") or {}).get("coding") or [{}]
    coding = c[0]
    enc_ref = ((res.get("encounter") or {}).get("reference") or '')
    return {
        "id": res.get("id"),
        "patient_id": ((res.get("subject") or {}).get("reference") or '').split('/')[-1],
        "encounter_id": enc_ref.split('/')[-1] if enc_ref else '',
        "medication_code": coding.get("code", ''),
        "medication_display": coding.get("display") or coding.get("code") or 'Unknown Medication',
        "medication_system": coding.get("system", ''),
        "status": res.get("status", ''),
        "intent": res.get("intent", ''),
        "priority": res.get("priority", ''),
        "authored_on": res.get("authoredOn", ''),
    }

def _map_med_admin(res: Dict[str, Any]) -> Dict[str, Any]:
    c = (res.get("medicationCodeableConcept") or {}).get("coding") or [{}]
    coding = c[0]
    ctx_ref = ((res.get("context") or {}).get("reference") or '')
    return {
        "id": res.get("id"),
        "patient_id": ((res.get("subject") or {}).get("reference") or '').split('/')[-1],
        "encounter_id": ctx_ref.split('/')[-1] if ctx_ref else '',
        "medication_code": coding.get("code", ''),
        "medication_display": coding.get("display") or coding.get("code") or 'Unknown Medication',
        "medication_system": coding.get("system", ''),
        "status": res.get("status", ''),
        "effective_start": res.get("effectiveDateTime") or ((res.get("effectivePeriod") or {}).get("start")) or '',
        "effective_end": ((res.get("effectivePeriod") or {}).get("end")) or '',
    }

def _within(ts: str, start: Optional[str], end: Optional[str]) -> bool:
    if not ts:
        return False
    try:
        t = time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))
        s = time.mktime(time.strptime(start[:19], "%Y-%m-%dT%H:%M:%S")) if start else None
        e = time.mktime(time.strptime(end[:19], "%Y-%m-%dT%H:%M:%S")) if end else None
        if s and t < s:
            return False
        if e and t > e:
            return False
        return True
    except Exception:
        return False

@app.get("/encounter/medications")
async def encounter_medications(patient: str, encounter: str, start: Optional[str] = None, end: Optional[str] = None):
    """Return both MedicationRequest and MedicationAdministration for an encounter.

    Follows pagination; if encounter search returns empty, fall back to patient
    scope and filter by encounter id or time window.
    """
    # Requests
    req_params = {"patient": patient, "encounter": encounter, "_count": 50}
    req_entries = await _fetch_all_pages("/MedicationRequest", req_params)
    if not req_entries:
        all_req = await _fetch_all_pages("/MedicationRequest", {"patient": patient, "_count": 50})
        req = [_map_med_req(e.get("resource", {})) for e in all_req]
        req = [r for r in req if r.get("encounter_id") == encounter.split('/')[-1] or _within(r.get("authored_on", ''), start, end)]
        req_note = "inferred-by-time-window"
    else:
        req = [_map_med_req(e.get("resource", {})) for e in req_entries]
        req_note = None

    # Administrations
    adm_params = {"patient": patient, "encounter": encounter, "_count": 50}
    adm_entries = await _fetch_all_pages("/MedicationAdministration", adm_params)
    if not adm_entries:
        all_adm = await _fetch_all_pages("/MedicationAdministration", {"patient": patient, "_count": 50})
        adm = [_map_med_admin(e.get("resource", {})) for e in all_adm]
        adm = [a for a in adm if a.get("encounter_id") == encounter.split('/')[-1] or _within(a.get("effective_start", ''), start, end)]
        adm_note = "inferred-by-time-window"
    else:
        adm = [_map_med_admin(e.get("resource", {})) for e in adm_entries]
        adm_note = None

    note = None
    if req_note or adm_note:
        note = "results include items inferred by time window"
    return {"requests": req, "administrations": adm, "note": note}

@app.get("/patients/summary")
async def patients_summary(patient: str):
    """Return counts per resource for a patient using _summary=count."""
    async def count(path: str) -> int:
        data = await fetch_from_fhir(path, {"patient": patient, "_summary": "count"})
        return int(data.get("total") or 0)
    return {
        "patient": patient,
        "summary": {
            "conditions": await count("/Condition"),
            "medications": await count("/MedicationRequest"),
            "encounters": await count("/Encounter"),
            "medication_administrations": await count("/MedicationAdministration"),
            "observations": await count("/Observation"),
            "procedures": await count("/Procedure"),
            "specimens": await count("/Specimen"),
        }
    }

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
    # Fetch from FHIR
    params = {"_count": _count}
    if name:
        params["name"] = name
    cache_key = build_cache_key("GET", "/Patient", params)
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
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

@app.post("/verify/encounters")
async def verify_encounters(payload: Dict):
    """Return Encounter totals per patient id using _summary=count.

    Body: {"ids": ["patient-id", ...]}
    """
    ids = payload.get("ids") or []
    if not isinstance(ids, list) or not ids:
        return {"status": "ok", "results": []}

    results: List[Dict] = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for pid in ids:
            try:
                url = f"{FHIR_BASE_URL}/Encounter"
                params = {"patient": f"Patient/{pid}", "_summary": "count"}
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    total = int(data.get("total") or 0)
                    results.append({"id": pid, "total": total})
                else:
                    results.append({"id": pid, "error": resp.text})
            except Exception as e:
                results.append({"id": pid, "error": str(e)})

    return {"status": "ok", "results": results}

@app.get("/Condition")
async def get_conditions(
    patient: Optional[str] = None,
    _count: Optional[int] = 100
):
    """Get conditions from FHIR server with caching"""
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    cache_key = build_cache_key("GET", "/Condition", params)
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
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
    encounter: Optional[str] = None,
    _count: Optional[int] = 100
):
    """Get medication requests from FHIR server with caching"""
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    if medication:
        params["medication"] = medication
    if encounter:
        params["encounter"] = encounter
    cache_key = build_cache_key("GET", "/MedicationRequest", params)
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
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
    encounter: Optional[str] = None,
    _count: Optional[int] = 100
):
    """Get medication administrations from FHIR server with caching"""
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    if encounter:
        params["encounter"] = encounter
    cache_key = build_cache_key("GET", "/MedicationAdministration", params)
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
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
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    cache_key = build_cache_key("GET", "/Encounter", params)
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
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
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    if code:
        params["code"] = code
    cache_key = build_cache_key("GET", "/Observation", params)
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
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
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    cache_key = build_cache_key("GET", "/Procedure", params)
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
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
    # Fetch from FHIR
    params = {"_count": _count}
    if patient:
        params["patient"] = patient
    cache_key = build_cache_key("GET", "/Specimen", params)
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            return cached_data["data"]
    
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
