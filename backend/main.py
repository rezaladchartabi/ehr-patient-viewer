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
import sqlite3
import pickle
import hashlib
from contextlib import asynccontextmanager

# Configuration
FHIR_BASE_URL = "https://gel-landscapes-impaired-vitamin.trycloudflare.com/fhir"
CACHE_TTL = 300  # 5 minutes cache
RATE_LIMIT_REQUESTS = 100  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds
MAX_CONNECTIONS = 20
CONNECTION_TIMEOUT = 30.0

# Global state
cache: Dict[str, Dict] = {}
rate_limit_tracker: Dict[str, List[float]] = defaultdict(list)
http_client: Optional[httpx.AsyncClient] = None

# Search index (SQLite FTS5)
SEARCH_DB_PATH = os.path.join(os.path.dirname(__file__), "search_index.sqlite3")

# Performance optimizations
class OptimizedCache:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, Dict] = {}
        self.access_order: List[str] = []
    
    def get(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Dict, ttl: int = CACHE_TTL):
        if len(self.cache) >= self.max_size:
            # Remove least recently used
            lru_key = self.access_order.pop(0)
            del self.cache[lru_key]
        
        self.cache[key] = {
            "data": value,
            "timestamp": time.time(),
            "ttl": ttl
        }
        self.access_order.append(key)
    
    def is_valid(self, key: str) -> bool:
        if key not in self.cache:
            return False
        entry = self.cache[key]
        return time.time() - entry["timestamp"] < entry["ttl"]
    
    def clear_expired(self):
        now = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now - entry["timestamp"] >= entry["ttl"]
        ]
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)

# Initialize optimized cache
optimized_cache = OptimizedCache(max_size=2000)

# Initialize FastAPI app
app = FastAPI(title="EHR FHIR Proxy", version="1.0.0")

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)

def _search_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(SEARCH_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_search_schema():
    conn = _search_conn()
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("PRAGMA cache_size=10000;")
    cur.execute("PRAGMA temp_store=MEMORY;")
    cur.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS si USING fts5(
            type,            -- 'patient' | 'medication-request' | 'medication-administration' | 'condition'
            patient_id,      -- Patient UUID
            rid,             -- resource id (or patient id for patient rows)
            title,           -- primary display (name or medication/condition display)
            subtitle,        -- secondary info (gender/birth or status/code)
            ts,              -- ISO datetime used for ordering
            tokenize='unicode61 remove_diacritics 2'
        );
        """
    )
    conn.commit()
    conn.close()

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
    return not path.startswith('/search') and 'cache' not in path

# Connection pool management
@asynccontextmanager
async def get_http_client():
    global http_client
    if http_client is None:
        limits = httpx.Limits(max_connections=MAX_CONNECTIONS, max_keepalive_connections=10)
        http_client = httpx.AsyncClient(
            limits=limits,
            timeout=CONNECTION_TIMEOUT,
            headers={"User-Agent": "EHR-Proxy/1.0"}
        )
    try:
        yield http_client
    except Exception:
        # Reset client on error
        if http_client:
            await http_client.aclose()
            http_client = None
        raise

async def fetch_from_fhir(path: str, params: Dict = None) -> Dict:
    """Fetch data from FHIR server with optimized connection pooling"""
    async with get_http_client() as client:
        url = f"{FHIR_BASE_URL}{path}"
        if params:
            query_string = urlencode(params, doseq=True)
            url = f"{url}?{query_string}"
        
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

def _cursor_allowed(cursor_url: str) -> bool:
    """Validate cursor URL for security"""
    try:
        parsed = urlparse(cursor_url)
        return parsed.netloc.endswith('trycloudflare.com') and parsed.path.startswith('/fhir')
    except:
        return False

@app.get("/paginate")
async def paginate(cursor: str):
    """Fetch a FHIR page via absolute 'next' link (cursor). Returns raw Bundle."""
    if not _cursor_allowed(cursor):
        raise HTTPException(status_code=400, detail="Invalid cursor host")

    cache_key = get_cache_key("GET", "/paginate", cursor)
    if optimized_cache.is_valid(cache_key):
        cached = optimized_cache.get(cache_key)
        if cached:
            return cached["data"]

    async with get_http_client() as client:
        response = await client.get(cursor)
        response.raise_for_status()
        data = response.json()

    optimized_cache.set(cache_key, data)
    return data

@app.on_event("startup")
async def _startup_client():
    global http_client
    if http_client is None:
        limits = httpx.Limits(max_connections=MAX_CONNECTIONS, max_keepalive_connections=10)
        http_client = httpx.AsyncClient(
            limits=limits,
            timeout=CONNECTION_TIMEOUT,
            headers={"User-Agent": "EHR-Proxy/1.0"}
        )
    ensure_search_schema()

@app.on_event("shutdown")
async def _shutdown_client():
    global http_client
    if http_client is not None:
        await http_client.aclose()
        http_client = None

async def _fetch_all_pages(path: str, params: Dict[str, Any]) -> List[Dict]:
    """Fetch first page and follow link[next] until exhausted. Returns entry list."""
    # First page
    first = await fetch_from_fhir(path, params)
    entries: List[Dict] = list(first.get("entry") or [])
    links = first.get("link") or []
    next_link = next((l.get("url") for l in links if l.get("relation") == "next"), None)
    # Follow next links using shared client (direct GET)
    if next_link:
        client = http_client or httpx.AsyncClient(timeout=30.0)
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

@app.get("/encounter/observations")
async def encounter_observations(patient: str, encounter: str, start: Optional[str] = None, end: Optional[str] = None):
    """Get observations for a specific encounter with time-window fallback"""
    # First try to get observations directly linked to the encounter
    params = {
        "patient": patient,
        "encounter": encounter,
        "_count": 100
    }
    
    try:
        data = await fetch_from_fhir("/Observation", params)
        observations = data.get("entry", [])
        
        # If we found observations, return them
        if observations:
            return {
                "observations": observations,
                "note": f"Found {len(observations)} observations directly linked to encounter"
            }
    except Exception as e:
        print(f"Error fetching encounter-linked observations: {e}")
    
    # Fallback: get observations within encounter time window
    if start and end:
        try:
            # Get observations for the patient within the time window
            time_params = {
                "patient": patient,
                "date": f"ge{start}&date=le{end}",
                "_count": 100
            }
            data = await fetch_from_fhir("/Observation", time_params)
            observations = data.get("entry", [])
            
            return {
                "observations": observations,
                "note": f"Found {len(observations)} observations within encounter time window ({start} to {end})"
            }
        except Exception as e:
            print(f"Error fetching time-window observations: {e}")
    
    return {
        "observations": [],
        "note": "No observations found for this encounter"
    }

@app.get("/encounter/procedures")
async def encounter_procedures(patient: str, encounter: str, start: Optional[str] = None, end: Optional[str] = None):
    """Get procedures for a specific encounter with time-window fallback"""
    # First try to get procedures directly linked to the encounter
    params = {
        "patient": patient,
        "encounter": encounter,
        "_count": 100
    }
    
    try:
        data = await fetch_from_fhir("/Procedure", params)
        procedures = data.get("entry", [])
        
        # If we found procedures, return them
        if procedures:
            return {
                "procedures": procedures,
                "note": f"Found {len(procedures)} procedures directly linked to encounter"
            }
    except Exception as e:
        print(f"Error fetching encounter-linked procedures: {e}")
    
    # Fallback: get procedures within encounter time window
    if start and end:
        try:
            # Get procedures for the patient within the time window
            time_params = {
                "patient": patient,
                "date": f"ge{start}&date=le{end}",
                "_count": 100
            }
            data = await fetch_from_fhir("/Procedure", time_params)
            procedures = data.get("entry", [])
            
            return {
                "procedures": procedures,
                "note": f"Found {len(procedures)} procedures within encounter time window ({start} to {end})"
            }
        except Exception as e:
            print(f"Error fetching time-window procedures: {e}")
    
    return {
        "procedures": [],
        "note": "No procedures found for this encounter"
    }

@app.get("/encounter/specimens")
async def encounter_specimens(patient: str, encounter: str, start: Optional[str] = None, end: Optional[str] = None):
    """Get specimens for a specific encounter with time-window fallback"""
    # First try to get specimens directly linked to the encounter
    params = {
        "patient": patient,
        "encounter": encounter,
        "_count": 100
    }
    
    try:
        data = await fetch_from_fhir("/Specimen", params)
        specimens = data.get("entry", [])
        
        # If we found specimens, return them
        if specimens:
            return {
                "specimens": specimens,
                "note": f"Found {len(specimens)} specimens directly linked to encounter"
            }
    except Exception as e:
        print(f"Error fetching encounter-linked specimens: {e}")
    
    # Fallback: get specimens within encounter time window
    if start and end:
        try:
            # Get specimens for the patient within the time window
            time_params = {
                "patient": patient,
                "collected": f"ge{start}&collected=le{end}",
                "_count": 100
            }
            data = await fetch_from_fhir("/Specimen", time_params)
            specimens = data.get("entry", [])
            
            return {
                "specimens": specimens,
                "note": f"Found {len(specimens)} specimens within encounter time window ({start} to {end})"
            }
        except Exception as e:
            print(f"Error fetching time-window specimens: {e}")
    
    return {
        "specimens": [],
        "note": "No specimens found for this encounter"
    }

def _si_insert(rows: List[Dict[str, Any]]):
    if not rows:
        return
    conn = _search_conn()
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO si(type,patient_id,rid,title,subtitle,ts) VALUES(?,?,?,?,?,?)",
        [(r.get('type'), r.get('patient_id'), r.get('rid'), r.get('title'), r.get('subtitle'), r.get('ts')) for r in rows]
    )
    conn.commit()
    conn.close()

def _si_clear_patient(pid: str):
    conn = _search_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM si WHERE patient_id=?", (pid,))
    conn.commit()
    conn.close()

@app.post("/search/update")
async def search_update(patient: str):
    """Refresh index rows for a single patient (Patient/{uuid})."""
    pid = patient.split('/')[-1]
    _si_clear_patient(pid)
    rows: List[Dict[str, Any]] = []
    # Patient row
    p = await fetch_from_fhir("/Patient", {"_id": pid, "_count": 1})
    for e in p.get("entry", []) or []:
        res = e.get("resource", {})
        name = ((res.get("name") or [{}])[0]).get("family") or ''
        gender = res.get("gender", '')
        bdate = res.get("birthDate", '')
        rid = res.get("id")
        rows.append({
            "type": "patient", "patient_id": rid, "rid": rid,
            "title": name or "Unknown", "subtitle": f"{gender} • {bdate}", "ts": bdate or ''
        })
    # Medications
    for path in ("/MedicationRequest", "/MedicationAdministration"):
        entries = await _fetch_all_pages(path, {"patient": f"Patient/{pid}", "_count": 50})
        for e in entries:
            res = e.get("resource", {})
            cc = ((res.get("medicationCodeableConcept") or {}).get("coding") or [{}])[0]
            display = cc.get("display") or cc.get("code") or ''
            status = res.get("status", '')
            rid = res.get("id")
            ts = res.get("authoredOn") or res.get("effectiveDateTime") or ((res.get("effectivePeriod") or {}).get("start")) or ''
            rows.append({
                "type": "medication-request" if path == "/MedicationRequest" else "medication-administration",
                "patient_id": pid, "rid": rid, "title": display, "subtitle": status, "ts": ts
            })
    # Conditions
    entries = await _fetch_all_pages("/Condition", {"patient": f"Patient/{pid}", "_count": 50})
    for e in entries:
        res = e.get("resource", {})
        code = ((res.get("code") or {}).get("coding") or [{}])[0]
        title = (res.get("code") or {}).get("text") or code.get("display") or code.get("code") or ''
        status = ((res.get("clinicalStatus") or {}).get("coding") or [{}])[0].get("code", '')
        rid = res.get("id")
        ts = res.get("recordedDate") or ''
        rows.append({
            "type": "condition", "patient_id": pid, "rid": rid, "title": title, "subtitle": status, "ts": ts
        })
    _si_insert(rows)
    return {"status": "ok", "indexed": len(rows)}

@app.post("/search/reindex")
async def search_reindex():
    """Rebuild the search index for allowlisted patients."""
    ids_env = os.getenv("ALLOWLIST_IDS", "").strip()
    if not ids_env:
        return {"status": "ok", "message": "no ALLOWLIST_IDS set", "indexed": 0}
    ids = [i.strip() for i in ids_env.split(',') if i.strip()]
    # Clear all
    conn = _search_conn(); cur = conn.cursor(); cur.execute("DELETE FROM si"); conn.commit(); conn.close()
    total = 0
    for pid in ids:
        r = await search_update(patient=f"Patient/{pid}")
        total += int(r.get("indexed") or 0)
    return {"status": "ok", "indexed": total}

@app.get("/search")
async def search_q(q: str, limit: int = 50):
    if not q or not q.strip():
        return {"items": []}
    q = q.strip()
    conn = _search_conn(); cur = conn.cursor()
    # Expand common synonyms/classes (e.g., statin → specific molecules)
    ql = q.lower()
    expansions = {
        'statin': ['atorvastatin','simvastatin','rosuvastatin','pravastatin','lovastatin','fluvastatin','pitavastatin'],
        'heparin': ['heparin','enoxaparin','dalteparin']
    }
    terms = [ql]
    for k, vals in expansions.items():
        if k in ql:
            terms.extend(vals)
    # Build FTS OR query with prefix matching
    or_query = ' OR '.join([t.replace('"','') + '*' for t in terms])
    cur.execute("SELECT type, patient_id, rid, title, subtitle, ts FROM si WHERE si MATCH ? ORDER BY ts DESC LIMIT ?", (or_query, limit))
    items = [dict(row) for row in cur.fetchall()]
    # Substring fallback (handles mid-word matches like 'statin')
    if not items:
        like = f"%{ql}%"
        cur.execute(
            "SELECT type, patient_id, rid, title, subtitle, ts FROM si WHERE lower(title) LIKE ? OR lower(subtitle) LIKE ? ORDER BY ts DESC LIMIT ?",
            (like, like, limit)
        )
        items = [dict(row) for row in cur.fetchall()]
    conn.close()
    return {"items": items}

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

            # Warm top recent encounters and medications per encounter
            try:
                enc_entries = await _fetch_all_pages("/Encounter", {"patient": f"Patient/{pid}", "_count": 50})
                # map with start for sorting
                def _start(e: Dict[str, Any]):
                    res = e.get("resource", {})
                    s = ((res.get("period") or {}).get("start")) or ''
                    try:
                        return time.mktime(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))
                    except Exception:
                        return 0
                enc_entries.sort(key=_start, reverse=True)
                recent_n = int(os.getenv("WARM_RECENT_ENCOUNTERS", "2"))
                for entry in enc_entries[:recent_n]:
                    res = entry.get("resource", {})
                    enc_id = res.get("id")
                    start = ((res.get("period") or {}).get("start")) or ''
                    end = ((res.get("period") or {}).get("end")) or ''
                    # trigger combined handler to warm
                    await encounter_medications(patient=f"Patient/{pid}", encounter=f"Encounter/{enc_id}", start=start, end=end)
            except Exception:
                pass

    return {"status": "ok", "counts": counts}

# Background scheduler to warm cache from allowlist
async def _scheduled_prefetch_loop():
    await asyncio.sleep(5)
    while True:
        try:
            ids_env = os.getenv("ALLOWLIST_IDS", "").strip()
            if ids_env:
                ids = [i.strip() for i in ids_env.split(',') if i.strip()]
                await prefetch_patients({"ids": ids, "force": False})
        except Exception:
            pass
        interval = int(os.getenv("PREFETCH_INTERVAL_MINUTES", "60"))
        await asyncio.sleep(interval * 60)

@app.on_event("startup")
async def _start_scheduler():
    asyncio.create_task(_scheduled_prefetch_loop())

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

@app.get("/search/patients")
async def search_patients(q: str, _count: int = 20):
    """Aggregate patient search across Patient + medication resources and dedupe by id."""
    if not q or not q.strip():
        return {"entry": [], "total": 0}
    q = q.strip()
    queries = [
        ("/Patient", {"name": q, "_count": _count}),
        ("/Patient", {"name:contains": q, "_count": _count}),
        ("/Patient", {"family": q, "_count": _count}),
        ("/Patient", {"family:contains": q, "_count": _count}),
        ("/Patient", {"identifier": q, "_count": _count}),
    ]
    # If UUID-ish, also try _id
    import re
    if re.match(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", q):
        queries.append(("/Patient", {"_id": q, "_count": _count}))

    results: Dict[str, Dict] = {}
    for path, params in queries:
        try:
            data = await fetch_from_fhir(path, params)
            for e in data.get("entry", []) or []:
                rid = (e.get("resource") or {}).get("id")
                if rid and rid not in results:
                    results[rid] = e
        except Exception:
            continue

    # Medication-backed search → find patients via MedicationRequest/Administration when text matches
    med_patient_ids: List[str] = []
    med_queries = [
        ("/MedicationRequest", {"_text": q, "_count": _count}),
        ("/MedicationAdministration", {"_text": q, "_count": _count}),
        ("/MedicationRequest", {"medication": q, "_count": _count}),
        ("/MedicationRequest", {"medication:text": q, "_count": _count}),
        ("/MedicationAdministration", {"medication:text": q, "_count": _count}),
    ]
    for path, params in med_queries:
        try:
            data = await fetch_from_fhir(path, params)
            for e in data.get("entry", []) or []:
                res = e.get("resource") or {}
                subj = (res.get("subject") or {}).get("reference") or ''
                pid = subj.split('/')[-1] if subj else ''
                if pid:
                    med_patient_ids.append(pid)
        except Exception:
            continue
    # Dedupe and fetch Patient resources for medication hits
    if med_patient_ids:
        uniq_ids = sorted(set(med_patient_ids))
        try:
            pats = await fetch_from_fhir("/Patient", {"_id": ",".join(uniq_ids), "_count": len(uniq_ids)})
            for e in pats.get("entry", []) or []:
                rid = (e.get("resource") or {}).get("id")
                if rid and rid not in results:
                    results[rid] = e
        except Exception:
            pass

    entries = list(results.values())
    # Fallback: scan allowlisted patients' meds for substring match when remote indexes don't return hits
    if not entries:
        ids_env = os.getenv("ALLOWLIST_IDS", "").strip()
        if ids_env:
            ids_list = [i.strip() for i in ids_env.split(',') if i.strip()]
            ql = q.lower()
            hit_patient_ids: List[str] = []
            # scan MedicationRequest and MedicationAdministration per patient
            for pid in ids_list:
                try:
                    # MedicationRequest
                    req_entries = await _fetch_all_pages("/MedicationRequest", {"patient": f"Patient/{pid}", "_count": 50})
                    def _req_hit(e: Dict[str, Any]):
                        res = e.get("resource", {})
                        cc = ((res.get("medicationCodeableConcept") or {}).get("coding") or [{}])[0]
                        texts = [
                            (cc.get("display") or ''),
                            (cc.get("code") or ''),
                            ((res.get("medicationCodeableConcept") or {}).get("text") or ''),
                        ]
                        return any(ql in (t or '').lower() for t in texts)
                    if any(_req_hit(e) for e in req_entries):
                        hit_patient_ids.append(pid)
                        continue  # enough to add once
                    # MedicationAdministration
                    adm_entries = await _fetch_all_pages("/MedicationAdministration", {"patient": f"Patient/{pid}", "_count": 50})
                    def _adm_hit(e: Dict[str, Any]):
                        res = e.get("resource", {})
                        cc = ((res.get("medicationCodeableConcept") or {}).get("coding") or [{}])[0]
                        texts = [
                            (cc.get("display") or ''),
                            (cc.get("code") or ''),
                            ((res.get("medicationCodeableConcept") or {}).get("text") or ''),
                        ]
                        return any(ql in (t or '').lower() for t in texts)
                    if any(_adm_hit(e) for e in adm_entries):
                        hit_patient_ids.append(pid)
                except Exception:
                    continue
            if hit_patient_ids:
                try:
                    pats = await fetch_from_fhir("/Patient", {"_id": ",".join(sorted(set(hit_patient_ids)))})
                    for e in pats.get("entry", []) or []:
                        rid = (e.get("resource") or {}).get("id")
                        if rid and rid not in results:
                            results[rid] = e
                    entries = list(results.values())
                except Exception:
                    pass
    return {"resourceType": "Bundle", "type": "searchset", "total": len(entries), "entry": entries}

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
