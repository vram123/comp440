
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

app = Flask(__name__)
app.secret_key = "change-me-in-production"  # For sessions & flash

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
                # determine which field likely failed
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

if __name__ == "__main__":
    app.run(debug=True)
