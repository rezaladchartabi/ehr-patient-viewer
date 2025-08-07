from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sqlite3
from typing import List, Dict
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "ehr_data.sqlite3")

app = FastAPI(title="EHR System API", version="1.0.0")

# Allow CORS for all origins (you can restrict this in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def read_root():
    return {"message": "EHR System API is running"}

@app.get("/patients", response_model=List[Dict])
def list_patients():
    conn = get_db_connection()
    patients = conn.execute("SELECT * FROM patient").fetchall()
    conn.close()
    return [dict(row) for row in patients]

@app.get("/patients/{patient_id}", response_model=Dict)
def get_patient(patient_id: str):
    conn = get_db_connection()
    patient = conn.execute("SELECT * FROM patient WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return dict(patient)

@app.get("/conditions", response_model=List[Dict])
def list_conditions():
    conn = get_db_connection()
    conditions = conn.execute("SELECT * FROM condition").fetchall()
    conn.close()
    return [dict(row) for row in conditions]

@app.get("/conditions/{condition_id}", response_model=Dict)
def get_condition(condition_id: str):
    conn = get_db_connection()
    condition = conn.execute("SELECT * FROM condition WHERE id = ?", (condition_id,)).fetchone()
    conn.close()
    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")
    return dict(condition)

@app.get("/patients/{patient_id}/conditions", response_model=List[Dict])
def get_patient_conditions(patient_id: str):
    conn = get_db_connection()
    conditions = conn.execute("SELECT * FROM condition WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in conditions]

@app.get("/medications", response_model=List[Dict])
def list_medications():
    conn = get_db_connection()
    medications = conn.execute("SELECT * FROM medication").fetchall()
    conn.close()
    return [dict(row) for row in medications]

@app.get("/medications/{medication_id}", response_model=Dict)
def get_medication(medication_id: str):
    conn = get_db_connection()
    medication = conn.execute("SELECT * FROM medication WHERE id = ?", (medication_id,)).fetchone()
    conn.close()
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    return dict(medication)

@app.get("/patients/{patient_id}/medications", response_model=List[Dict])
def get_patient_medications(patient_id: str):
    conn = get_db_connection()
    medications = conn.execute("SELECT * FROM medication WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in medications]

# Encounter endpoints
@app.get("/encounters", response_model=List[Dict])
def list_encounters():
    conn = get_db_connection()
    encounters = conn.execute("SELECT * FROM encounter").fetchall()
    conn.close()
    return [dict(row) for row in encounters]

@app.get("/encounters/{encounter_id}", response_model=Dict)
def get_encounter(encounter_id: str):
    conn = get_db_connection()
    encounter = conn.execute("SELECT * FROM encounter WHERE id = ?", (encounter_id,)).fetchone()
    conn.close()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return dict(encounter)

@app.get("/patients/{patient_id}/encounters", response_model=List[Dict])
def get_patient_encounters(patient_id: str):
    conn = get_db_connection()
    encounters = conn.execute("SELECT * FROM encounter WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in encounters]

# Medication Administration endpoints
@app.get("/medication-administrations", response_model=List[Dict])
def list_medication_administrations():
    conn = get_db_connection()
    administrations = conn.execute("SELECT * FROM medication_administration").fetchall()
    conn.close()
    return [dict(row) for row in administrations]

@app.get("/medication-administrations/{admin_id}", response_model=Dict)
def get_medication_administration(admin_id: str):
    conn = get_db_connection()
    administration = conn.execute("SELECT * FROM medication_administration WHERE id = ?", (admin_id,)).fetchone()
    conn.close()
    if not administration:
        raise HTTPException(status_code=404, detail="Medication administration not found")
    return dict(administration)

@app.get("/patients/{patient_id}/medication-administrations", response_model=List[Dict])
def get_patient_medication_administrations(patient_id: str):
    conn = get_db_connection()
    administrations = conn.execute("SELECT * FROM medication_administration WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in administrations]

# Medication Request endpoints
@app.get("/medication-requests", response_model=List[Dict])
def list_medication_requests():
    conn = get_db_connection()
    requests = conn.execute("SELECT * FROM medication_request").fetchall()
    conn.close()
    return [dict(row) for row in requests]

@app.get("/medication-requests/{request_id}", response_model=Dict)
def get_medication_request(request_id: str):
    conn = get_db_connection()
    request = conn.execute("SELECT * FROM medication_request WHERE id = ?", (request_id,)).fetchone()
    conn.close()
    if not request:
        raise HTTPException(status_code=404, detail="Medication request not found")
    return dict(request)

@app.get("/patients/{patient_id}/medication-requests", response_model=List[Dict])
def get_patient_medication_requests(patient_id: str):
    conn = get_db_connection()
    requests = conn.execute("SELECT * FROM medication_request WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in requests]

# Observation endpoints
@app.get("/observations", response_model=List[Dict])
def list_observations():
    conn = get_db_connection()
    observations = conn.execute("SELECT * FROM observation LIMIT 1000").fetchall()  # Limit for performance
    conn.close()
    return [dict(row) for row in observations]

@app.get("/observations/{observation_id}", response_model=Dict)
def get_observation(observation_id: str):
    conn = get_db_connection()
    observation = conn.execute("SELECT * FROM observation WHERE id = ?", (observation_id,)).fetchone()
    conn.close()
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")
    return dict(observation)

@app.get("/patients/{patient_id}/observations", response_model=List[Dict])
def get_patient_observations(patient_id: str):
    conn = get_db_connection()
    observations = conn.execute("SELECT * FROM observation WHERE patient_id = ? LIMIT 500", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in observations]

# Procedure endpoints
@app.get("/procedures", response_model=List[Dict])
def list_procedures():
    conn = get_db_connection()
    procedures = conn.execute("SELECT * FROM procedure").fetchall()
    conn.close()
    return [dict(row) for row in procedures]

@app.get("/procedures/{procedure_id}", response_model=Dict)
def get_procedure(procedure_id: str):
    conn = get_db_connection()
    procedure = conn.execute("SELECT * FROM procedure WHERE id = ?", (procedure_id,)).fetchone()
    conn.close()
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return dict(procedure)

@app.get("/patients/{patient_id}/procedures", response_model=List[Dict])
def get_patient_procedures(patient_id: str):
    conn = get_db_connection()
    procedures = conn.execute("SELECT * FROM procedure WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in procedures]

# Specimen endpoints
@app.get("/specimens", response_model=List[Dict])
def list_specimens():
    conn = get_db_connection()
    specimens = conn.execute("SELECT * FROM specimen").fetchall()
    conn.close()
    return [dict(row) for row in specimens]

@app.get("/specimens/{specimen_id}", response_model=Dict)
def get_specimen(specimen_id: str):
    conn = get_db_connection()
    specimen = conn.execute("SELECT * FROM specimen WHERE id = ?", (specimen_id,)).fetchone()
    conn.close()
    if not specimen:
        raise HTTPException(status_code=404, detail="Specimen not found")
    return dict(specimen)

@app.get("/patients/{patient_id}/specimens", response_model=List[Dict])
def get_patient_specimens(patient_id: str):
    conn = get_db_connection()
    specimens = conn.execute("SELECT * FROM specimen WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in specimens]

# Dashboard endpoint for patient summary
@app.get("/patients/{patient_id}/summary", response_model=Dict)
def get_patient_summary(patient_id: str):
    conn = get_db_connection()
    
    # Get patient info
    patient = conn.execute("SELECT * FROM patient WHERE id = ?", (patient_id,)).fetchone()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get counts for each data type
    condition_count = conn.execute("SELECT COUNT(*) FROM condition WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    medication_count = conn.execute("SELECT COUNT(*) FROM medication WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    encounter_count = conn.execute("SELECT COUNT(*) FROM encounter WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    medication_admin_count = conn.execute("SELECT COUNT(*) FROM medication_administration WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    medication_request_count = conn.execute("SELECT COUNT(*) FROM medication_request WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    observation_count = conn.execute("SELECT COUNT(*) FROM observation WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    procedure_count = conn.execute("SELECT COUNT(*) FROM procedure WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    specimen_count = conn.execute("SELECT COUNT(*) FROM specimen WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    
    conn.close()
    
    return {
        "patient": dict(patient),
        "summary": {
            "conditions": condition_count,
            "medications": medication_count,
            "encounters": encounter_count,
            "medication_administrations": medication_admin_count,
            "medication_requests": medication_request_count,
            "observations": observation_count,
            "procedures": procedure_count,
            "specimens": specimen_count
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
