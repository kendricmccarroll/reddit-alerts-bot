from flask import Flask, render_template, request, redirect, session
from scanner import scan_reddit, load_user_config, save_user_config, get_all_users



import uuid
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

@app.route("/")
def index():
    user_id = session.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4())
        session["user_id"] = user_id
        save_user_config(user_id, {"keywords": [], "subreddits": []})
    config = load_user_config(user_id)
    return render_template("index.html", config=config)

@app.route("/add", methods=["POST"])
def add():
    user_id = session.get("user_id")
    config = load_user_config(user_id)
    if "keyword" in request.form and request.form["keyword"]:
        config["keywords"].append(request.form["keyword"])
    if "subreddit" in request.form and request.form["subreddit"]:
        config["subreddits"].append(request.form["subreddit"])
    save_user_config(user_id, config)
    return redirect("/")

@app.route("/delete", methods=["POST"])
def delete():
    user_id = session.get("user_id")
    config = load_user_config(user_id)
    if "keyword" in request.form:
        config["keywords"].remove(request.form["keyword"])
    if "subreddit" in request.form:
        config["subreddits"].remove(request.form["subreddit"])
    save_user_config(user_id, config)
    return redirect("/")

@app.route("/scan", methods=["POST"])
def trigger_scan():
    user_id = session.get("user_id")
    scan_reddit(user_id)
    return redirect("/")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        for uid in get_all_users():
            scan_reddit(uid)
    else:
        app.run(debug=True, port=8080)
