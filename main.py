"""GETBACk: entirely synthetic Nigerian transfer and fraud-analyst training."""
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="GETBACk Analyst Academy — Simulation Only")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

SCENARIOS = {
    "routine": {
        "title": "Routine family transfer", "channel": "Mobile banking", "bank": "Fictional Bank A",
        "amount": 125000, "source": "DEMO-1001", "beneficiary": "DEMO-2001",
        "beneficiary_name": "Chika Okoro", "name_match": True, "balance": 900000,
        "device": "Known device", "location": "Usual location", "history": "Similar monthly transfers",
        "otp": "Passed", "limit": 500000, "instant_enabled": True,
        "signals": [], "risk": "Low", "expected": "release", "outcome": "Credited",
        "lesson": "Recognize normal activity and avoid unnecessary disruption to a legitimate customer.",
    },
    "new_device": {
        "title": "High value on a newly activated device", "channel": "Mobile banking", "bank": "Fictional Bank A",
        "amount": 8500000, "source": "DEMO-1002", "beneficiary": "DEMO-2002",
        "beneficiary_name": "Demo Holdings", "name_match": True, "balance": 12000000,
        "device": "Activated 2 hours ago", "location": "New location", "history": "Usually below ₦450,000",
        "otp": "Passed", "limit": 20000, "instant_enabled": True,
        "signals": ["Newly activated device", "Above temporary device limit", "Large change from usual activity", "New beneficiary"],
        "risk": "Critical", "expected": "hold", "outcome": "Held before dispatch",
        "lesson": "A passed OTP does not override a device limit or other risk controls.",
    },
    "name_mismatch": {
        "title": "Beneficiary name mismatch", "channel": "Internet banking", "bank": "Fictional Bank B",
        "amount": 620000, "source": "DEMO-1003", "beneficiary": "DEMO-2003",
        "beneficiary_name": "Returned name differs from intended payee", "name_match": False, "balance": 2200000,
        "device": "Known device", "location": "Usual location", "history": "First payment to beneficiary",
        "otp": "Passed", "limit": 2000000, "instant_enabled": True,
        "signals": ["Name enquiry mismatch", "First payment to beneficiary"],
        "risk": "High", "expected": "hold", "outcome": "Stopped before dispatch",
        "lesson": "Confirm a beneficiary mismatch before any transfer instruction is sent.",
    },
    "rapid_repeat": {
        "title": "Rapid repeated transfers", "channel": "Mobile banking", "bank": "Fictional Bank B",
        "amount": 480000, "source": "DEMO-1004", "beneficiary": "DEMO-2004",
        "beneficiary_name": "Fictional Trader", "name_match": True, "balance": 3000000,
        "device": "Known device", "location": "Usual location", "history": "Five similar attempts in 8 minutes",
        "otp": "Passed", "limit": 1000000, "instant_enabled": True,
        "signals": ["Rapid sequence of similar transfers", "New beneficiary", "Cumulative amount requires review"],
        "risk": "High", "expected": "hold", "outcome": "Held for investigation",
        "lesson": "Review cumulative activity, not only the amount of a single transfer.",
    },
    "uncertain": {
        "title": "Debit with uncertain credit", "channel": "USSD", "bank": "Fictional Bank A",
        "amount": 75000, "source": "DEMO-1005", "beneficiary": "DEMO-2005",
        "beneficiary_name": "Tunde Bello", "name_match": True, "balance": 400000,
        "device": "Registered phone", "location": "Unknown via USSD", "history": "Ordinary amount",
        "otp": "Channel authorization passed", "limit": 200000, "instant_enabled": True,
        "signals": ["Timeout after debit", "Beneficiary credit unconfirmed"],
        "risk": "Operational exception", "expected": "query", "outcome": "Status initially uncertain; simulated query: pending investigation",
        "lesson": "Query the existing transaction status before any retry or customer assurance.",
    },
    "disabled": {
        "title": "Customer disabled instant transfers", "channel": "Mobile banking", "bank": "Fictional Bank B",
        "amount": 320000, "source": "DEMO-1006", "beneficiary": "DEMO-2006",
        "beneficiary_name": "Ada Ibrahim", "name_match": True, "balance": 800000,
        "device": "Known device", "location": "Usual location", "history": "Ordinary amount",
        "otp": "Passed", "limit": 1000000, "instant_enabled": False,
        "signals": ["Instant payment disabled by customer"],
        "risk": "Control block", "expected": "hold", "outcome": "Blocked by customer preference",
        "lesson": "Respect customer payment preferences; follow the bank's authenticated change process.",
    },
}
ACTIONS = {"release": "Release", "hold": "Hold and escalate", "query": "Query existing status"}

@dataclass
class Case:
    scenario_id: str
    created_at: float
    events: list[str] = field(default_factory=list)
    decision: str | None = None
    rationale: str = ""
    score: int | None = None

CASES: dict[str, Case] = {}
PROJECTS: dict[str, dict] = {}
FINDINGS: dict[str, dict] = {}
AUDIT: list[dict] = []

def record(event: str, ref: str):
    AUDIT.append({"time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), "event": event, "ref": ref})



def render(request: Request, name: str = "index.html", **context):
    return templates.TemplateResponse(request=request, name=name, context={"scenarios": SCENARIOS, "actions": ACTIONS, **context})

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render(request, recent=list(reversed(list(CASES.items())[-6:])), projects=PROJECTS, findings=FINDINGS, audit=list(reversed(AUDIT[-12:])))

@app.post("/cases")
def create_case(scenario_id: str = Form(...), project_id: str = Form(...)):
    if scenario_id not in SCENARIOS:
        raise HTTPException(400, "Unknown training scenario")
    project = PROJECTS.get(project_id)
    if not project or project["status"] != "Approved (demo record)":
        raise HTTPException(403, "Create an approved demo scope before starting a case")
    if scenario_id not in project["scenarios"]:
        raise HTTPException(403, "Scenario is outside this demo project scope")
    case_id = secrets.token_urlsafe(12)
    s = SCENARIOS[scenario_id]
    CASES[case_id] = Case(scenario_id, time.time(), [
        f"Customer initiated {s['channel']} request",
        f"Name enquiry: {'match' if s['name_match'] else 'mismatch'}",
        f"Authorization signal: {s['otp']}",
        "Risk engine evaluated the transaction",
        f"Analyst alert opened: {s['risk']}",
    ])
    record("Training case opened", case_id)
    return RedirectResponse(f"/cases/{case_id}", status_code=303)

@app.get("/cases/{case_id}", response_class=HTMLResponse)
def view_case(request: Request, case_id: str):
    case = CASES.get(case_id)
    if case is None:
        raise HTTPException(404, "Training case not found; demo sessions clear on restart")
    return render(request, case=case, case_id=case_id, scenario=SCENARIOS[case.scenario_id])

@app.post("/cases/{case_id}/decide")
def decide(case_id: str, action: Literal["release", "hold", "query"] = Form(...), rationale: str = Form(...)):
    case = CASES.get(case_id)
    if case is None:
        raise HTTPException(404, "Training case not found")
    if case.decision is not None:
        raise HTTPException(409, "Decision already recorded")
    if len(rationale.strip()) < 15 or len(rationale) > 1000:
        raise HTTPException(400, "Explain your decision in 15 to 1000 characters")
    scenario = SCENARIOS[case.scenario_id]
    case.decision = action
    case.rationale = rationale.strip()
    case.score = 100 if action == scenario["expected"] else 35
    case.events.append(f"Analyst decision: {ACTIONS[action]}")
    record("Analyst decision recorded", case_id)
    case.events.append(f"Simulated disposition: {scenario['outcome'] if action == scenario['expected'] else 'Incorrect decision; trainer review required'}")
    return RedirectResponse(f"/cases/{case_id}", status_code=303)


@app.post("/projects")
def create_project(name: str = Form(...), scope: str = Form(...), authorization_ref: str = Form(...), scenarios: list[str] = Form(...)):
    if not 3 <= len(name.strip()) <= 80 or not 15 <= len(scope.strip()) <= 800:
        raise HTTPException(400, "Provide a project name and detailed synthetic test scope")
    if not 5 <= len(authorization_ref.strip()) <= 80:
        raise HTTPException(400, "Provide a demo authorization reference")
    allowed = sorted(set(scenarios) & set(SCENARIOS))
    if not allowed:
        raise HTTPException(400, "Select at least one scenario")
    project_id = secrets.token_urlsafe(9)
    PROJECTS[project_id] = {"name": name.strip(), "scope": scope.strip(), "authorization_ref": authorization_ref.strip(), "scenarios": allowed, "status": "Pending review"}
    record("Demo project proposed", project_id)
    return RedirectResponse("/", status_code=303)

@app.post("/projects/{project_id}/approve")
def demo_approve(project_id: str, reviewer: str = Form(...)):
    project = PROJECTS.get(project_id)
    if project is None:
        raise HTTPException(404, "Project not found")
    if not 3 <= len(reviewer.strip()) <= 80:
        raise HTTPException(400, "Enter a demo reviewer name")
    project["status"] = "Approved (demo record)"
    project["reviewer"] = reviewer.strip()
    record("Demo scope marked approved by " + reviewer.strip(), project_id)
    return RedirectResponse("/", status_code=303)

@app.post("/findings")
def add_finding(project_id: str = Form(...), title: str = Form(...), severity: str = Form(...), evidence: str = Form(...), recommendation: str = Form(...)):
    if project_id not in PROJECTS or PROJECTS[project_id]["status"] != "Approved (demo record)":
        raise HTTPException(403, "An approved demo project is required")
    if severity not in {"Low", "Medium", "High", "Critical"}:
        raise HTTPException(400, "Invalid severity")
    if not 5 <= len(title.strip()) <= 120 or not 15 <= len(evidence.strip()) <= 1000 or not 15 <= len(recommendation.strip()) <= 1000:
        raise HTTPException(400, "Provide a title, evidence and remediation recommendation")
    finding_id = secrets.token_urlsafe(9)
    FINDINGS[finding_id] = {"project_id": project_id, "title": title.strip(), "severity": severity, "evidence": evidence.strip(), "recommendation": recommendation.strip(), "status": "Open"}
    record("Demo finding created", finding_id)
    return RedirectResponse("/", status_code=303)

@app.post("/findings/{finding_id}/status")
def finding_status(finding_id: str, status: str = Form(...)):
    finding = FINDINGS.get(finding_id)
    if finding is None or status not in {"Open", "In remediation", "Ready for retest", "Closed"}:
        raise HTTPException(400, "Unknown finding or status")
    finding["status"] = status
    record("Finding changed to " + status, finding_id)
    return RedirectResponse("/", status_code=303)

@app.get("/report", response_class=HTMLResponse)
def report(request: Request):
    return render(request, name="report.html", projects=PROJECTS, findings=FINDINGS, cases=CASES, audit=AUDIT)

@app.get("/health")
def health():
    return {"status": "ok", "mode": "simulation"}
