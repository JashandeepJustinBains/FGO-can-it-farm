Consolidated FastAPI POC
=========================

Purpose
-------
This small POC consolidates the simulation FastAPI and a subset of the Flask data endpoints into a single FastAPI app. The goal is to let clients call `/simulate` and `/api/*` from one service and remove the previous HTTP forwarding from Flask to FastAPI.

Files added/changed
- `api/db.py` - MongoDB helper. Initializes `MongoClient` with `MONGO_URI` env var and exposes collections.
- `api/main.py` - Extended FastAPI app that keeps `/simulate` and adds several `/api/*` GET endpoints.

Environment
-----------
Required environment variables:
- `MONGO_URI` - MongoDB connection string

Optional:
- Any env used by the simulation code (same as before)

Run locally (development)
-------------------------
1. Create and activate a Python virtual environment (if you use one) and install requirements:

    powershell
    python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt

2. Start the FastAPI app with uvicorn from the repository root:

    powershell
    set MONGO_URI in your environment, for example (PowerShell):
    $env:MONGO_URI = 'mongodb://<your-uri>'
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

3. Test endpoints:

- POST http://localhost:8000/simulate (JSON body matching the SimRequest Pydantic model)
- GET http://localhost:8000/api/servants
- GET http://localhost:8000/api/mysticcodes

Notes & next steps
------------------
- This POC ports only a subset of the Flask endpoints. After validation, port the remaining endpoints (quests, filters, logs).
- If simulations remain fast, there's no need for async/background workers. If you want async job handling later, add a small queue (RQ/Celery) and an endpoint to poll job status.
- Update frontend to call `/simulate` directly and remove the Flask proxy.

If you'd like, I can continue porting all endpoints, add tests, and update Docker and k8s manifests.
