import os
from functools import wraps
import threading

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.utils import secure_filename
from pypdf import PdfReader

from database import (
    init_db, create_user, get_user, save_profile,
    get_profile, save_analysis, get_latest_analysis,
    load_jobs, get_job
)
from graph import build_graph
from agents import _fallback_response

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

init_db()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        user_id = create_user(name, email, password)

        if not user_id:
            flash("Email already registered.", "danger")
            return render_template("register.html")

        session["user_id"] = user_id
        session["name"] = name
        return redirect(url_for("profile"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = get_user(email, password)

        if not user:
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["name"] = user["name"]
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    profile = get_profile(session["user_id"])
    analysis = get_latest_analysis(session["user_id"])
    jobs = load_jobs()

    return render_template(
        "dashboard.html",
        profile=profile,
        analysis=analysis,
        jobs_count=len(jobs),
    )


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    existing = get_profile(session["user_id"])

    if request.method == "POST":
        data = {
            "education": request.form.get("education", ""),
            "experience": request.form.get("experience", ""),
            "skills": request.form.get("skills", ""),
            "projects": request.form.get("projects", ""),
            "target_role": request.form.get("target_role", ""),
            "resume_text": existing.get("resume_text", "") if existing else "",
        }

        save_profile(session["user_id"], data)
        flash("Profile saved successfully.", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", profile=existing)


@app.route("/resume", methods=["GET", "POST"])
@login_required
def resume():
    profile = get_profile(session["user_id"])

    if request.method == "POST":
        file = request.files.get("resume")

        if not file or file.filename == "":
            flash("Please select a PDF resume.", "danger")
            return redirect(url_for("resume"))

        if not file.filename.lower().endswith(".pdf"):
            flash("Only PDF files are supported.", "danger")
            return redirect(url_for("resume"))

        try:
            reader = PdfReader(file)
            text = "\n".join(
                page.extract_text() or "" for page in reader.pages
            )

            data = profile or {
                "education": "",
                "experience": "",
                "skills": "",
                "projects": "",
                "target_role": "",
            }

            data["resume_text"] = text
            save_profile(session["user_id"], data)

            flash("Resume uploaded and text extracted.", "success")
        except Exception as exc:
            flash(f"Could not read PDF: {exc}", "danger")

        return redirect(url_for("resume"))

    return render_template("resume.html", profile=profile)


def _run_analysis(user_id, career_profile, jobs):
    graph = build_graph()
    state = {
        "profile": career_profile,
        "jobs_text": jobs.to_string(index=False),
        "profile_analysis": "",
        "job_matching": "",
        "skill_gap": "",
        "roadmap": "",
        "interview": "",
        "final_report": "",
    }

    try:
        result = graph.invoke(state)
    except Exception as exc:
        result = {
            "profile_analysis": _fallback_response("profile analysis"),
            "job_matching": _fallback_response("job matching"),
            "skill_gap": _fallback_response("skill gaps"),
            "roadmap": _fallback_response("roadmap"),
            "interview": _fallback_response("interview prep"),
            "final_report": _fallback_response("final report"),
        }
    save_analysis(user_id, result)


@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    profile = get_profile(session["user_id"])

    if not profile:
        flash("Complete your profile first.", "warning")
        return redirect(url_for("profile"))

    jobs = load_jobs()

    career_profile = {
        "name": session.get("name", ""),
        "education": profile.get("education", ""),
        "experience": profile.get("experience", ""),
        "skills": profile.get("skills", ""),
        "projects": profile.get("projects", ""),
        "target_role": profile.get("target_role", ""),
        "resume_text": profile.get("resume_text", ""),
    }

    placeholder = {
        "profile_analysis": "AI career analysis has started. Results may take up to 2 minutes. This page will refresh automatically.",
        "job_matching": "AI career analysis has started. Results may take up to 2 minutes. This page will refresh automatically.",
        "skill_gap": "AI career analysis has started. Results may take up to 2 minutes. This page will refresh automatically.",
        "roadmap": "AI career analysis has started. Results may take up to 2 minutes. This page will refresh automatically.",
        "interview": "AI career analysis has started. Results may take up to 2 minutes. This page will refresh automatically.",
        "final_report": "AI career analysis has started. Results may take up to 2 minutes. This page will refresh automatically.",
    }
    save_analysis(session["user_id"], placeholder)

    thread = threading.Thread(
        target=_run_analysis,
        args=(session["user_id"], career_profile, jobs),
        daemon=True,
    )
    thread.start()

    flash("AI career analysis has started. Results will appear shortly.", "info")
    return redirect(url_for("results"))


@app.route("/results")
@login_required
def results():
    analysis = get_latest_analysis(session["user_id"])

    if not analysis:
        return redirect(url_for("dashboard"))

    return render_template("results.html", analysis=analysis)


@app.route("/jobs")
@login_required
def jobs():
    jobs_df = load_jobs()

    search = request.args.get("search", "").strip().lower()
    location = request.args.get("location", "").strip().lower()

    if search:
        mask = (
            jobs_df["role"].str.lower().str.contains(search, na=False)
            | jobs_df["skills"].str.lower().str.contains(search, na=False)
            | jobs_df["company"].str.lower().str.contains(search, na=False)
        )
        jobs_df = jobs_df[mask]

    if location:
        jobs_df = jobs_df[
            jobs_df["location"].str.lower().str.contains(location, na=False)
        ]

    return render_template(
        "jobs.html",
        jobs=jobs_df.to_dict("records"),
        search=search,
        location=location,
    )


@app.route("/jobs/<job_id>")
@login_required
def job_details(job_id):
    job = get_job(job_id)

    if not job:
        flash("Job not found.", "danger")
        return redirect(url_for("jobs"))

    return render_template("job_details.html", job=job)


@app.route("/interview")
@login_required
def interview():
    analysis = get_latest_analysis(session["user_id"])
    return render_template("interview.html", analysis=analysis)


@app.route("/api/jobs")
@login_required
def api_jobs():
    jobs = load_jobs().to_dict("records")
    return jsonify(jobs)


if __name__ == "__main__":
    app.run(debug=True)
