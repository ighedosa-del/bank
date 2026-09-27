# GETBACk / OMEGA — Nigerian Transfer & Fraud Analyst Training

An integrated, fictional demonstration for a bank pitch. It combines end-to-end transfer scenarios, fraud alert investigation, a demo project and scope register, mock approval records, findings and remediation status, an event trail, and a printable report.

## Included training scenarios

- Routine legitimate transfer and false-positive avoidance
- Large amount on a newly activated device
- Beneficiary name mismatch
- Rapid repeated transfers and cumulative activity
- Debit with uncertain beneficiary credit and status query
- Customer-disabled instant payments

The simulator models customer initiation, beneficiary name enquiry, authorization result, risk signals, analyst decision, and disposition. Analyst decisions are scored against illustrative expected responses. These examples are **not** any bank's actual rules.

## Demo boundaries

All identities and accounts are synthetic. There is no NIBSS connection, real OTP, customer credential collection, scanning, real bank login, or money movement. "Approved (demo record)" is a user-entered teaching state, **not verified authorization** to test a real institution. This public prototype has no user login, identity-verified reviewer, durable evidence store, or production audit controls. Do not use it to certify bank staff or manage an actual penetration test.

For a bank deployment, get the bank's written scope and controls, implement authenticated roles and independent approvals, encrypted persistent storage, tenant separation, immutable audit retention, policy versioning, incident escalation, and security review. Bank-specific limit and risk settings must be configured by the bank.

## Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000. On Render, deploy the root repository with the included Dockerfile. `/health` is available for a basic service check. The prototype holds demo projects, cases, and findings in process memory; restarting clears them.
