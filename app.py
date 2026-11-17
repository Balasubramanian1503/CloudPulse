import os
from functools import wraps
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from database import init_db, create_user, get_user, add_incident, get_incidents, save_metric, get_history, has_recent_high_cpu
from monitor import get_metrics

load_dotenv()
app=Flask(__name__)
app.secret_key=os.getenv("SECRET_KEY","replace-this-before-deployment")
app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE="Lax",PERMANENT_SESSION_LIFETIME=3600)
init_db()
THRESHOLD=float(os.getenv("CPU_THRESHOLD", "80"))

def signed_in(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.","info")
            return redirect(url_for("login"))
        return fn(*args,**kwargs)
    return wrapper

@app.route("/")
def home():
    return redirect(url_for("dashboard" if session.get("user_id") else "login"))

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower(); password=request.form.get("password",""); confirm=request.form.get("confirm_password","")
        if not name or not email or not password: flash("Complete all fields.","error")
        elif len(password)<8: flash("Password must contain at least 8 characters.","error")
        elif password!=confirm: flash("Passwords do not match.","error")
        elif get_user(email): flash("An account with this email already exists.","error")
        else:
            create_user(name,email,generate_password_hash(password)); flash("Account created. Please sign in.","success"); return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        user=get_user(request.form.get("email","").strip().lower())
        if user and check_password_hash(user["password_hash"],request.form.get("password","")):
            session.clear(); session["user_id"]=user["id"]; session["user_name"]=user["name"]; session.permanent=True
            return redirect(url_for("dashboard"))
        flash("Email or password is incorrect.","error")
    return render_template("login.html")

@app.route("/logout",methods=["POST"])
@signed_in
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/dashboard")
@signed_in
def dashboard(): return render_template("index.html",user_name=session.get("user_name"),threshold=THRESHOLD)

@app.route("/api/metrics")
@signed_in
def metrics():
    mode=os.getenv("MONITOR_MODE","demo").lower()
    try:
        data=get_metrics(mode); data["threshold"]=THRESHOLD; data["mode"]=mode
        if data.get("cpu") is not None:
            save_metric(data["cpu"],data.get("memory"),data.get("status","UNKNOWN"))
            if data["cpu"]>=THRESHOLD:
                if not has_recent_high_cpu(minutes=10):
                    add_incident("HIGH_CPU",f"CPU utilization reached {data['cpu']:.1f}% (threshold: {THRESHOLD:.1f}%).","Critical")
                data["alert"]=True
            else: data["alert"]=False
        return jsonify(data)
    except Exception:
        app.logger.exception("Monitoring request failed")
        return jsonify({"error":"Could not retrieve metrics. Check AWS configuration and application logs.","mode":mode}),503

@app.route("/api/incidents")
@signed_in
def incidents(): return jsonify(get_incidents())

@app.route("/api/history")
@signed_in
def history(): return jsonify(get_history())

@app.route("/api/test-alert",methods=["POST"])
@signed_in
def test_alert():
    add_incident("TEST_ALERT","Manual test alert generated from the dashboard.","Warning")
    return jsonify({"ok":True,"message":"Test incident recorded."})

if __name__=="__main__":
    app.run(host="127.0.0.1",port=5000,debug=os.getenv("FLASK_DEBUG","false").lower()=="true")
