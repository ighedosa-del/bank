# GETBACk OMEGA — synthetic bank transfer and fraud control lab

A working presentation demo for training fraud analysts and testing **illustrative** transfer controls. It includes a dense command dashboard, fictional account ledger, expected-versus-actual detection test, held-transfer analyst review, six guided investigations, scoped demo projects, synthetic findings, remediation, activity trail and printable report.

## Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000. Render can deploy the root repository using the included Dockerfile. `/health` reports service status.

## Demonstration sequence

1. On Transfer simulator, select built-in DEMO source and receiving accounts, amount, and expected result. Click Run. Inspect PASS or FAIL, triggered signals, and synthetic balances.
2. If the transfer is held, choose a demo analyst disposition and record a rationale.
3. In Projects & scope, create a synthetic assessment scope and record its demo review; then run one of six cases in Case lab.
4. Record a fictional finding and update remediation status. Open Audit trail and Print report.

## Boundaries

Only built-in `DEMO-` accounts are accepted. There are no actual bank numbers, customers, OTPs, external APIs, payment networks, or money movement. Tests compare a user-selected expected result with this app's own illustrative rule engine; they do not test a bank's live controls. Demo approval is self-recorded and **not verified authorization** for any external testing. All records are in process memory and clear when Render restarts. The app has no user authentication and is not ready for real bank data or operational use.

For a bank deployment, implement authenticated role separation, independent approval, tenant isolation, persistent encrypted records, immutable audit, policy configuration, bank sandbox adapters, and a reviewed test plan under written authorization.
