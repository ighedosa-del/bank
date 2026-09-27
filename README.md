# GETBACk Transfer Simulator

This is a fictional training prototype. It does not collect passwords, connect to a bank, send messages, or move funds. Use only made-up account numbers.

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000. Render can deploy this repository using `render.yaml`.

Demo sessions live in process memory and are cleared on service restart. This is a prototype, not a multi-user training platform.
