
# COMP 440 — Course Project Phase 1 (Flask + SQLite)

Implements signup and login with:
- **Schema**: `user(username, password_hash, firstName, lastName, email, phone)` — `username` is the primary key; `email` and `phone` are **UNIQUE**.
- **Security**: parameterized SQL (prevents SQL injection) + hashed passwords.
- **Validations**: password confirmation; duplicate `username`/`email`/`phone` detection.

## Quickstart

```bash
# 1) Create & activate a virtualenv (recommended)
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install deps
pip install -r requirements.txt

# 3) Initialize the DB
python init_db.py

# 4) Run the app
python app.py
# open http://127.0.0.1:5000
```

## Where SQL injection is prevented
All DB operations use parameterized queries, e.g.:
```python
conn.execute("SELECT * FROM user WHERE username = ?", (username,))
```
**Never** string‑format user input into SQL.

## Deliverables
- Zip your source as `COMP440_TeamNo_P1.zip` (include source and a README).
- Record a short YouTube demo using any screen recorder (voice only is fine).

## Optional: Git commands to push
```bash
git init
git remote add origin https://github.com/vram123/comp440.git
git add .
git commit -m "Phase 1: signup/login with parameterized SQL + hashed passwords"
git branch -M main
git push -u origin main
```
