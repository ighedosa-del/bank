import secrets
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="GETBACk Bank Transfer Simulator")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
BANKS = {"gtbank": "GTBank (simulation)", "uba": "UBA (simulation)"}

@dataclass
class Transfer:
    bank_name: str
    target_account: str
    amount: Decimal
    otp: str
    created_at: float
    completed: bool = False

sessions: dict[str, Transfer] = {}

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"banks": BANKS})

@app.post("/transfer", response_class=HTMLResponse)
def transfer(request: Request, bank_name: str = Form(...), target_account: str = Form(...), amount: str = Form(...)):
    if bank_name not in BANKS:
        raise HTTPException(400, "Unsupported demo bank")
    if not (target_account.isdigit() and len(target_account) == 10):
        raise HTTPException(400, "Enter a 10-digit fictional account number")
    try:
        value = Decimal(amount)
    except InvalidOperation:
        raise HTTPException(400, "Invalid amount")
    if not (Decimal("0") < value <= Decimal("100000000")):
        raise HTTPException(400, "Amount outside demo limits")
    session_id = secrets.token_urlsafe(24)
    otp = f"{secrets.randbelow(1000000):06d}"
    sessions[session_id] = Transfer(bank_name, target_account, value, otp, time.time())
    return templates.TemplateResponse(request=request, name="index.html", context={"banks": BANKS, "status": "OTP Required", "session_id": session_id, "demo_otp": otp})

@app.post("/verify", response_class=HTMLResponse)
def verify(request: Request, session_id: str = Form(...), otp: str = Form(...)):
    item = sessions.get(session_id)
    if item is None:
        raise HTTPException(404, "Demo session not found")
    if item.completed:
        raise HTTPException(409, "Demo transfer already completed")
    if time.time() - item.created_at > 300:
        sessions.pop(session_id, None)
        raise HTTPException(400, "Demo OTP expired")
    if not secrets.compare_digest(otp, item.otp):
        raise HTTPException(400, "Incorrect demo OTP")
    item.completed = True
    return templates.TemplateResponse(request=request, name="index.html", context={"banks": BANKS, "status": "Success — simulated transfer only", "completed_transfer": item})
