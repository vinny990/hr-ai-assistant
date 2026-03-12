from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os
from rag import load_pdf, load_csv, chunk_text, build_index, search, answer_vulnerable, answer_secure
from validator import validate_input
from database import init_db, save_feedback, get_all_feedback, get_thumbs_down
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = "hr-assistant-secret-key"

init_db()

print("Loading HR policy PDF...")
policy_text = load_pdf("uploads/hr_policy.pdf")

print("Loading employee records CSV...")
employee_text = load_csv("uploads/employee_records.csv")

all_text = policy_text + "\n\n" + employee_text
chunks = chunk_text(all_text)

print("Building search index...")
embeddings = build_index(chunks)
print(f"Ready. {len(chunks)} chunks indexed.")

USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "employee": {"password": "demo123", "role": "employee"}
}

def get_current_user():
    return session.get("user")

def is_admin():
    user = get_current_user()
    return user and USERS.get(user, {}).get("role") == "admin"

@app.route("/")
def home():
    if not get_current_user():
        return redirect(url_for("login"))
    return render_template("index.html", 
        is_admin=is_admin(),
        username=get_current_user()
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = USERS.get(username)
        if user and user["password"] == password:
            session["user"] = username
            return redirect(url_for("home"))
        error = "Invalid username or password"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/ask", methods=["POST"])
def ask():
    if not get_current_user():
        return jsonify({"error": "Please login first"}), 401

    data = request.json
    question = data.get("question", "").strip()
    mode = data.get("mode", "secure")

    if not question:
        return jsonify({"error": "Please ask a question"}), 400

    if mode == "secure":
        is_valid, error_message = validate_input(question)
        if not is_valid:
            return jsonify({"answer": error_message})

    relevant_chunks = search(question, chunks, embeddings)

    if mode == "vulnerable":
        response = answer_vulnerable(question, relevant_chunks)
    else:
        response = answer_secure(question, relevant_chunks)

    return jsonify({"answer": response})

@app.route("/feedback", methods=["POST"])
def feedback():
    if not get_current_user():
        return jsonify({"error": "Please login first"}), 401
    data = request.json
    question = data.get("question", "")
    answer = data.get("answer", "")
    rating = data.get("rating", "")
    mode = data.get("mode", "secure")
    if not all([question, answer, rating]):
        return jsonify({"error": "Missing data"}), 400
    save_feedback(question, answer, rating, mode)
    return jsonify({"status": "saved"})

@app.route("/upload", methods=["POST"])
def upload():
    if not is_admin():
        return jsonify({"error": "Admin access required"}), 403

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF files allowed"}), 400

    global chunks, embeddings, all_text, policy_text

    filepath = os.path.join("uploads", file.filename)
    file.save(filepath)

    # Scan for PII
    import re
    raw_text = load_pdf(filepath)
    pii_found = []
    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", raw_text):
        pii_found.append("SSN patterns detected")
    if re.search(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", raw_text):
        pii_found.append("Phone number patterns detected")

    if pii_found:
        os.remove(filepath)
        return jsonify({
            "error": f"Upload rejected — PII detected: {', '.join(pii_found)}. Please remove sensitive data before uploading."
        }), 400

    # Re-index
    policy_text = raw_text
    all_text = policy_text + "\n\n" + employee_text
    chunks = chunk_text(all_text)
    embeddings = build_index(chunks)

    return jsonify({"status": f"{file.filename} uploaded and indexed successfully. {len(chunks)} chunks ready."})

@app.route("/dashboard")
def dashboard():
    if not is_admin():
        return redirect(url_for("home"))
    thumbs_down = get_thumbs_down()
    all_feedback = get_all_feedback()
    total = len(all_feedback)
    bad = len(thumbs_down)
    good = total - bad
    return render_template("dashboard.html",
        thumbs_down=thumbs_down,
        total=total,
        good=good,
        bad=bad
    )

if __name__ == "__main__":
    app.run(debug=True)
