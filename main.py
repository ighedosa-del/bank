"""GETBACk: entirely synthetic Nigerian transfer and fraud-analyst training."""
import secrets
import time
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from threading import Lock
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="GETBACk Analyst Academy — Simulation Only")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

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
LEDGER_LOCK = Lock()
DEMO_ACCOUNTS = {
    "DEMO-SOURCE-01": {"name": "Fictional customer A", "balance": 12000000, "device": "known", "usual": 400000, "limit": 10000000},
    "DEMO-SOURCE-02": {"name": "Fictional customer B", "balance": 900000, "device": "new", "usual": 120000, "limit": 20000},
    "DEMO-SOURCE-03": {"name": "Fictional business C", "balance": 6000000, "device": "known", "usual": 1500000, "limit": 5000000},
    "DEMO-RECEIVER-01": {"name": "Known beneficiary", "balance": 100000, "flagged": False},
    "DEMO-RECEIVER-02": {"name": "New beneficiary", "balance": 0, "flagged": False},
    "DEMO-RECEIVER-03": {"name": "Training watchlist account", "balance": 0, "flagged": True},
}
TRANSFERS: dict[str, dict] = {}


def record(event: str, ref: str):
    AUDIT.append({"time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), "event": event, "ref": ref})



def render(request: Request, name: str = "index.html", **context):
    return templates.TemplateResponse(request=request, name=name, context={"scenarios": SCENARIOS, "actions": ACTIONS, **context})

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render(request, recent=list(reversed(list(CASES.items())[-8:])), projects=PROJECTS, findings=FINDINGS, audit=list(reversed(AUDIT[-15:])), completed=sum(c.decision is not None for c in CASES.values()), accounts=DEMO_ACCOUNTS, transfers=list(reversed(list(TRANSFERS.items())[-12:])), transfer_count=len(TRANSFERS))

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
    return render(request, name="report.html", projects=PROJECTS, findings=FINDINGS, cases=CASES, audit=AUDIT, transfers=TRANSFERS)


@app.post("/transfers")
def simulate_transfer(source_account: str = Form(...), drop_account: str = Form(...), amount: str = Form(...), expected_status: Literal["Credited", "Held", "Blocked", "Declined"] = Form(...)):
    # Only synthetic accounts from this app can be selected or submitted.
    if source_account not in {"DEMO-SOURCE-01", "DEMO-SOURCE-02", "DEMO-SOURCE-03"} or drop_account not in {"DEMO-RECEIVER-01", "DEMO-RECEIVER-02", "DEMO-RECEIVER-03"}:
        raise HTTPException(400, "Only the built-in fictional accounts are accepted")
    try:
        value = Decimal(amount)
    except InvalidOperation:
        raise HTTPException(400, "Invalid amount")
    if not value.is_finite() or value != value.quantize(Decimal("0.01")) or not (Decimal("0") < value <= Decimal("100000000")):
        raise HTTPException(400, "Enter a positive amount of at most ₦100,000,000 with two decimal places")
    with LEDGER_LOCK:
        sender, receiver = DEMO_ACCOUNTS[source_account], DEMO_ACCOUNTS[drop_account]
        signals = []
        if receiver["flagged"]: signals.append("Beneficiary on synthetic watchlist")
        if sender["device"] == "new": signals.append("Newly activated device")
        if value > Decimal(str(sender["usual"] * 3)): signals.append("Amount far above usual activity")
        if drop_account != "DEMO-RECEIVER-01": signals.append("Unfamiliar beneficiary")
        if value > Decimal(str(sender["balance"])):
            status, reason = "Declined", "Insufficient fictional balance"
        elif value > Decimal(str(sender["limit"])):
            status, reason = "Blocked", "Above this demo account's limit"
        elif receiver["flagged"] or (sender["device"] == "new" and value > 10000) or (len(signals) >= 2 and value > 100000):
            status, reason = "Held", "Risk signals require analyst review"
        else:
            sender["balance"] -= value
            receiver["balance"] += value
            status, reason = "Credited", "Controls passed; fictional ledger updated"
        transfer_id = secrets.token_urlsafe(10)
        TRANSFERS[transfer_id] = {"source": source_account, "destination": drop_account, "amount": value,
            "status": status, "reason": reason, "signals": signals, "created": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "expected_status": expected_status, "test_result": "PASS" if status == expected_status else "FAIL",
            "events": ["Instruction created in synthetic ledger", "Demo balance and limits checked", "Detection rules evaluated", "Disposition: " + status]}
        record("Synthetic transfer " + status.lower(), transfer_id)
    return RedirectResponse("/transfers/" + transfer_id, status_code=303)

@app.get("/transfers/{transfer_id}", response_class=HTMLResponse)
def transfer_detail(request: Request, transfer_id: str):
    transaction = TRANSFERS.get(transfer_id)
    if transaction is None:
        raise HTTPException(404, "Demo transfer not found")
    return render(request, name="transfer.html", transaction=transaction, transfer_id=transfer_id, accounts=DEMO_ACCOUNTS)

@app.post("/transfers/{transfer_id}/review")
def review_transfer(transfer_id: str, action: Literal["release", "decline"] = Form(...), rationale: str = Form(...)):
    if not 15 <= len(rationale.strip()) <= 1000:
        raise HTTPException(400, "Provide a rationale of 15 to 1000 characters")
    with LEDGER_LOCK:
        tx = TRANSFERS.get(transfer_id)
        if tx is None:
            raise HTTPException(404, "Demo transfer not found")
        if tx["status"] != "Held":
            raise HTTPException(409, "Only held demo transfers can be reviewed")
        # Synthetic watchlist cases cannot be released by an analyst in this demo.
        if action == "release" and DEMO_ACCOUNTS[tx["destination"]]["flagged"]:
            raise HTTPException(403, "Demo watchlist control requires an independent review")
        if action == "release":
            sender = DEMO_ACCOUNTS[tx["source"]]
            if sender["balance"] < tx["amount"]:
                raise HTTPException(409, "Demo balance changed; cannot release")
            sender["balance"] -= tx["amount"]
            DEMO_ACCOUNTS[tx["destination"]]["balance"] += tx["amount"]
            tx["status"] = "Credited after review"
        else:
            tx["status"] = "Declined after review"
        tx["review_rationale"] = rationale.strip()
        tx["events"].append("Analyst review: " + tx["status"])
        record("Synthetic transfer reviewed", transfer_id)
    return RedirectResponse("/transfers/" + transfer_id, status_code=303)

@app.get("/health")
def health():
    return {"status": "ok", "mode": "simulation"}
