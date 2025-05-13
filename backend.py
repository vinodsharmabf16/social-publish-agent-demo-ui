from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# Allow Gradio to call this locally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# SAVE_DIR = "./drafts"
# os.makedirs(SAVE_DIR, exist_ok=True)

@app.post("/save_draft")
async def save_draft(request: Request):
    data = await request.json()
    account_id = data.get("account_id", "unknown")
    print(f"📝 Saving draft for account {account_id}")
    print(json.dumps(data, indent=2))
    
    # with open(f"{SAVE_DIR}/account_{account_id}.json", "w") as f:
    #     json.dump(data, f, indent=2)
    
    return {"status": "saved"}

@app.post("/publish")
async def publish(request: Request):
    data = await request.json()
    print("🚀 Publishing with data:")
    print(json.dumps(data, indent=2))
    return {"status": "published"}

