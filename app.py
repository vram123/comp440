from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from db import get_db

app = Flask(__name__)
app.secret_key = "change-me-in-production"  # For sessions & flash

# ---------- helpers ----------
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

# ---------- phase 1 ----------
@app.route("/")
def index():
    user = session.get("user")
    return render_template("home.html", user=user)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        firstName = request.form.get("firstName", "").strip()
        lastName = request.form.get("lastName", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()

        # Passwords must match
        if password != password_confirm:
            flash("Passwords do not match.", "error")
            return render_template("signup.html", form=request.form)

        # Basic presence checks
        if not all([username, password, firstName, lastName, email, phone]):
            flash("All fields are required.", "error")
            return render_template("signup.html", form=request.form)

        pw_hash = generate_password_hash(password)

        # Use parameterized queries to prevent SQL injection
        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO user (username, password_hash, firstName, lastName, email, phone) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (username, pw_hash, firstName, lastName, email, phone),
                )
                conn.commit()
            flash("Signup successful. Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            # Duplicate detection for username/email/phone via UNIQUE constraints
            msg = str(e).lower()
            if "unique constraint" in msg or "unique failed" in msg or "constraint failed" in msg:
                failed_field = "username/email/phone"
                if "user.username" in msg:
                    failed_field = "username"
                elif "user.email" in msg:
                    failed_field = "email"
                elif "user.phone" in msg:
                    failed_field = "phone"
                flash(f"Duplicate {failed_field}. Please choose a different value.", "error")
            else:
                flash("Signup failed. Please try again.", "error")
        return render_template("signup.html", form=request.form)

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as conn:
            row = conn.execute("SELECT * FROM user WHERE username = ?", (username,)).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session["user"] = dict(username=row["username"], firstName=row["firstName"], lastName=row["lastName"])
            flash("Login successful.", "success")
            return redirect(url_for("index"))
        flash("Invalid username or password.", "error")
        return render_template("login.html", form=request.form)
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

# ---------- phase 2 ----------
# Create blog (limit: <= 2 blogs/day per user)
@app.route("/blogs/new", methods=["GET", "POST"])
@login_required
def blogs_new():
    if request.method == "POST":
        owner = session["user"]["username"]
        subject = (request.form.get("subject") or "").strip()
        description = (request.form.get("description") or "").strip()
        tags_csv = (request.form.get("tags") or "").strip()

        if not subject or not description:
            flash("Subject and description are required.", "error")
            return render_template("blogs_new.html", form=request.form)

        with get_db() as conn:
            # Count today's blogs by this user
            c = conn.execute(
                "SELECT COUNT(*) AS c FROM blog WHERE owner=? AND date(created_at)=date('now','localtime')",
                (owner,)
            ).fetchone()["c"]
            if c >= 2:
                flash("Daily blog limit reached (2/day).", "error")
                return render_template("blogs_new.html", form=request.form)

            cur = conn.execute(
                "INSERT INTO blog (owner, subject, description) VALUES (?, ?, ?)",
                (owner, subject, description)
            )
            blog_id = cur.lastrowid

            # Insert tags (comma-separated)
            tags = [t.strip().lower() for t in tags_csv.split(",") if t.strip()]
            for t in tags:
                conn.execute("INSERT OR IGNORE INTO blog_tag (blog_id, tag) VALUES (?, ?)", (blog_id, t))
            conn.commit()

        flash("Blog posted.", "success")
        return redirect(url_for("blog_detail", blog_id=blog_id))

    return render_template("blogs_new.html")

# Search blogs by tag
@app.route("/blogs/search", methods=["GET", "POST"])
def blogs_search():
    results = []
    q = ""
    if request.method == "POST":
        q = (request.form.get("tag") or "").strip().lower()
        if q:
            with get_db() as conn:
                results = conn.execute("""
                    SELECT b.id, b.subject, b.owner, date(b.created_at) AS d
                    FROM blog b
                    JOIN blog_tag t ON t.blog_id = b.id
                    WHERE t.tag = ?
                    ORDER BY b.created_at DESC
                """, (q,)).fetchall()
        else:
            flash("Enter a tag to search.", "error")
    return render_template("blogs_search.html", tag=q, results=results)

# Blog detail + comments (rules: <=3/day, <=1 per blog/user, no self-comment)
@app.route("/blogs/<int:blog_id>", methods=["GET", "POST"])
@login_required
def blog_detail(blog_id):
    user = session["user"]
    with get_db() as conn:
        blog = conn.execute("SELECT * FROM blog WHERE id=?", (blog_id,)).fetchone()
        if not blog:
            flash("Blog not found.", "error")
            return redirect(url_for("blogs_search"))
        comments = conn.execute("""
            SELECT c.*, u.firstName || ' ' || u.lastName AS reviewer_name
            FROM comment c
            JOIN user u ON u.username = c.reviewer
            WHERE c.blog_id = ?
            ORDER BY c.created_at DESC
        """, (blog_id,)).fetchall()

    if request.method == "POST":
        reviewer = user["username"]
        sentiment = (request.form.get("sentiment") or "").lower()
        text = (request.form.get("description") or "").strip()

        if sentiment not in ("positive", "negative"):
            flash("Choose a sentiment.", "error")
            return render_template("blog_detail.html", blog=blog, comments=comments)
        if not text:
            flash("Comment text is required.", "error")
            return render_template("blog_detail.html", blog=blog, comments=comments)

        with get_db() as conn:
            # No self-comment
            owner = conn.execute("SELECT owner FROM blog WHERE id=?", (blog_id,)).fetchone()["owner"]
            if owner == reviewer:
                flash("You cannot comment on your own blog.", "error")
                return render_template("blog_detail.html", blog=blog, comments=comments)

            # <= 3 comments today by this user
            daily = conn.execute("""
                SELECT COUNT(*) AS c
                FROM comment
                WHERE reviewer=? AND date(created_at)=date('now','localtime')
            """, (reviewer,)).fetchone()["c"]
            if daily >= 3:
                flash("Daily comment limit reached (3/day).", "error")
                return render_template("blog_detail.html", blog=blog, comments=comments)

            # <= 1 comment on this blog by this user
            exists = conn.execute(
                "SELECT 1 FROM comment WHERE blog_id=? AND reviewer=?",
                (blog_id, reviewer)
            ).fetchone()
            if exists:
                flash("You already commented on this blog.", "error")
                return render_template("blog_detail.html", blog=blog, comments=comments)

            conn.execute("""
                INSERT INTO comment (blog_id, reviewer, sentiment, description)
                VALUES (?, ?, ?, ?)
            """, (blog_id, reviewer, sentiment, text))
            conn.commit()

        flash("Comment added.", "success")
        return redirect(url_for("blog_detail", blog_id=blog_id))

    return render_template("blog_detail.html", blog=blog, comments=comments)

# ---------- phase 3 ----------
@app.route("/reports")
@login_required
def reports_home():
    return render_template("reports/reports_home.html")

# Q1 — users who posted two blogs on same day with tag X and Y
@app.route("/reports/q1", methods=["GET","POST"])
@login_required
def report_q1():
    rows = []
    tag1 = tag2 = ""
    if request.method == "POST":
        tag1 = request.form.get("tag1","").strip().lower()
        tag2 = request.form.get("tag2","").strip().lower()
        if tag1 and tag2:
            with get_db() as conn:
                rows = conn.execute("""
                    SELECT DISTINCT b1.owner
                    FROM blog b1
                    JOIN blog_tag t1 ON t1.blog_id=b1.id
                    JOIN blog b2 ON b2.owner=b1.owner AND date(b1.created_at)=date(b2.created_at)
                    JOIN blog_tag t2 ON t2.blog_id=b2.id
                    WHERE t1.tag=? AND t2.tag=? AND b1.id<>b2.id
                """,(tag1,tag2)).fetchall()
    return render_template("reports/report_q1.html", rows=rows, tag1=tag1, tag2=tag2)

# Q2 — users who posted most blogs on a given date
@app.route("/reports/q2", methods=["GET","POST"])
@login_required
def report_q2():
    rows=[]; date=""
    if request.method=="POST":
        date=request.form.get("date","")
        if date:
            with get_db() as conn:
                rows=conn.execute("""
                    WITH counts AS (
                      SELECT owner,COUNT(*) c
                      FROM blog WHERE date(created_at)=date(?)
                      GROUP BY owner
                    ),
                    maxc AS (SELECT MAX(c) m FROM counts)
                    SELECT owner FROM counts,maxc WHERE c=m;
                """,(date,)).fetchall()
    return render_template("reports/report_q2.html", rows=rows, date=date)

# Q3 — users followed by both X and Y
@app.route("/reports/q3", methods=["GET","POST"])
@login_required
def report_q3():
    rows=[]; f1=f2=""
    if request.method=="POST":
        f1=request.form.get("f1","").strip()
        f2=request.form.get("f2","").strip()
        if f1 and f2:
            with get_db() as conn:
                rows=conn.execute("""
                    SELECT u.username
                    FROM user u
                    WHERE EXISTS(SELECT 1 FROM follow f WHERE f.followee=u.username AND f.follower=?)
                      AND EXISTS(SELECT 1 FROM follow f WHERE f.followee=u.username AND f.follower=?)
                """,(f1,f2)).fetchall()
    return render_template("reports/report_q3.html", rows=rows, f1=f1, f2=f2)

# Q4 — users who never posted a blog
@app.route("/reports/q4")
@login_required
def report_q4():
    with get_db() as conn:
        rows=conn.execute("""
            SELECT u.username
            FROM user u LEFT JOIN blog b ON b.owner=u.username
            WHERE b.id IS NULL;
        """).fetchall()
    return render_template("reports/report_q4.html", rows=rows)

# Q5 — blogs of user X with all-positive comments
@app.route("/reports/q5", methods=["GET","POST"])
@login_required
def report_q5():
    rows=[]; userx=""
    if request.method=="POST":
        userx=request.form.get("userx","").strip()
        if userx:
            with get_db() as conn:
                rows=conn.execute("""
                    SELECT b.id,b.subject
                    FROM blog b
                    JOIN comment c ON c.blog_id=b.id
                    WHERE b.owner=?
                    GROUP BY b.id
                    HAVING COUNT(*)>0
                       AND SUM(CASE WHEN c.sentiment='negative' THEN 1 ELSE 0 END)=0;
                """,(userx,)).fetchall()
    return render_template("reports/report_q5.html", rows=rows, userx=userx)

# Q6 — users whose every comment is negative
@app.route("/reports/q6")
@login_required
def report_q6():
    with get_db() as conn:
        rows=conn.execute("""
            SELECT c.reviewer
            FROM comment c
            GROUP BY c.reviewer
            HAVING COUNT(*)>0
               AND SUM(CASE WHEN c.sentiment='positive' THEN 1 ELSE 0 END)=0;
        """).fetchall()
    return render_template("reports/report_q6.html", rows=rows)

# Q7 — users whose blogs never received negative comments
@app.route("/reports/q7")
@login_required
def report_q7():
    with get_db() as conn:
        rows=conn.execute("""
            SELECT b.owner
            FROM blog b
            GROUP BY b.owner
            HAVING COUNT(*)>0
               AND SUM(
                 CASE WHEN EXISTS(
                   SELECT 1 FROM comment c WHERE c.blog_id=b.id AND c.sentiment='negative'
                 ) THEN 1 ELSE 0 END
               )=0;
        """).fetchall()
    return render_template("reports/report_q7.html", rows=rows)

# ---------- FOLLOW (for Phase 3) ----------

@app.route("/follow", methods=["GET", "POST"])
@login_required
def follow_page():
    current = session["user"]["username"]
    message_user = ""

    if request.method == "POST":
        action = request.form.get("action")
        target = (request.form.get("target") or "").strip()

        if not target:
            flash("Please enter a username.", "error")
        elif target == current:
            flash("You cannot follow yourself.", "error")
        else:
            with get_db() as conn:
                # Check that target user exists
                exists = conn.execute(
                    "SELECT 1 FROM user WHERE username = ?",
                    (target,)
                ).fetchone()
                if not exists:
                    flash("User does not exist.", "error")
                else:
                    if action == "follow":
                        try:
                            conn.execute(
                                "INSERT INTO follow (follower, followee) VALUES (?, ?)",
                                (current, target),
                            )
                            conn.commit()
                            flash(f"You are now following {target}.", "success")
                        except Exception:
                            # Primary key prevents duplicates
                            flash(f"You are already following {target}.", "info")
                    elif action == "unfollow":
                        conn.execute(
                            "DELETE FROM follow WHERE follower = ? AND followee = ?",
                            (current, target),
                        )
                        conn.commit()
                        flash(f"If you were following {target}, it has been removed.", "success")

        message_user = target

    # Load follower/following lists
    with get_db() as conn:
        following = conn.execute("""
            SELECT u.username, u.firstName, u.lastName
            FROM follow f
            JOIN user u ON u.username = f.followee
            WHERE f.follower = ?
            ORDER BY u.username
        """, (current,)).fetchall()

        followers = conn.execute("""
            SELECT u.username, u.firstName, u.lastName
            FROM follow f
            JOIN user u ON u.username = f.follower
            WHERE f.followee = ?
            ORDER BY u.username
        """, (current,)).fetchall()

    return render_template(
        "follow.html",
        following=following,
        followers=followers,
        last_target=message_user,
    )


# ---------- main ----------
if __name__ == "__main__":
    # Bind to 0.0.0.0 so it works in Docker too
    import os
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "1") == "1",
    )
