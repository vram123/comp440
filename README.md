# COMP 440 — Course Project (Phases 1 & 2)

Flask + SQLite web application implementing:
- **Phase 1:** secure user registration & login (hashed passwords + SQL-injection prevention)
- **Phase 2:** blogs, tags, comments, and per-day posting limits

---

## ⚙️ Technologies
- Python 3.11  
- Flask 3.0+  
- SQLite 3 (default)  
- Docker + Docker Compose (for portable runtime)

---

## 🧰 Implemented Features

### Phase 1 — Authentication
- Table `user(username, password_hash, firstName, lastName, email, phone)`  
  - `username` = Primary Key  
  - `email`, `phone` = UNIQUE  
- Password hashing with `werkzeug.security.generate_password_hash()` / `check_password_hash()`  
- Parameterized queries (prevents SQL injection)  
- Duplicate username/email/phone handling  
- Simple Flask GUI for Sign Up & Login

### Phase 2 — Blogs & Comments
- **Blogs**
  - `blog(id, owner, subject, description, created_at)`
  - Limit ≤ 2 blogs/day per user  
- **Tags**
  - `blog_tag(blog_id, tag)` — search blogs by tag  
- **Comments**
  - `comment(id, blog_id, reviewer, sentiment, description, created_at)`
  - Sentiment = positive or negative  
  - ≤ 3 comments/day per user  
  - ≤ 1 comment/blog per user (UNIQUE constraint)  
  - No self-comments on own blogs  
- All implemented via Flask templates + enhanced CSS UI  

---

## 🧭 How to Run the Project

### Option 1 — Run Locally (Without Docker)

> 💡 Requires Python 3.11 + pip

```bash
# 1 — Clone or unzip the project
cd comp440

# 2 — Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows  
# or: source .venv/bin/activate  # macOS/Linux

# 3 — Install dependencies
pip install -r requirements.txt

# 4 — Initialize the database
python init_db.py

# 5 — Run the app
python app.py
```

### Option 2 — Run with Docker (Recommended)

Requires Docker Desktop 4.30+ or Docker Engine + Compose v2
```bash
# Build the image
docker compose build

# Run the container
docker compose up -d

# View logs or stop
docker compose logs -f
docker compose down