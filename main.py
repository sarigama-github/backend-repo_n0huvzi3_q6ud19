from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Dict, Any

from database import db, create_document, get_documents
import schemas as app_schemas

app = FastAPI(title="Swiss Insurance Broker API", version="1.0.0")

# CORS (allow all origins for development; adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> Dict[str, Any]:
    return {"status": "ok", "service": "broker-backend"}


@app.get("/test")
def test_db() -> Dict[str, Any]:
    try:
        if db is None:
            raise Exception("Database not configured")
        # Ping by listing collections
        _ = db.list_collection_names()
        return {"database": "connected"}
    except Exception as e:
        return {"database": "unavailable", "error": str(e)}


@app.get("/schema")
def get_schema():
    # Introspect pydantic models defined in schemas.py (exclude builtins)
    models = {}
    for name in dir(app_schemas):
        attr = getattr(app_schemas, name)
        if isinstance(attr, type) and issubclass(attr, BaseModel) and attr is not BaseModel:
            try:
                models[name] = attr.model_json_schema()
            except Exception:
                pass
    return {"models": models}


# Contact/Lead submission
@app.post("/contact")
def create_lead(payload: app_schemas.Lead):
    try:
        lead_id = create_document("lead", payload)
        return {"ok": True, "id": lead_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leads")
def list_leads(limit: int = 20):
    try:
        docs = get_documents("lead", limit=limit)
        # Convert ObjectId to str for safety
        for d in docs:
            if "_id" in d:
                d["_id"] = str(d["_id"])
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
