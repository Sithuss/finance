from flask import Flask, redirect, render_template, request
import cs50
from flask_mail import Mail, Message

db = cs50.SQL("sqlite:///sports.db")

app = Flask(__name__)

SPORTS = [
    "football",
    "judo",
    "swimming"
]

@app.route("/")
def index():
    return render_template("index.html", sports = SPORTS)

@app.route("/registration", methods=["POST"])
def registration():
    name = request.form.get("name")
    if not name:
        return render_template("error.html", message="missing name")
    
    email = request.form.get("email")
    if not email:
        return render_template("error.html", message="missing email")
    
    sport = request.form.get("sport")
    if not sport:
        return render_template("error.html", message="missing sport")
    if not sport in SPORTS:
        return render_template("error.html", message="invalid sport")

    db.execute("INSERT INTO registrants (name, sport) VALUES (?, ?)",name, sport)

    return redirect("/registrants")  

@app.route("/registrants")
def registrants():
    registrants = db.execute("SELECT * FROM registrants")
    return render_template("registrants.html", registrants=registrants)

@app.route("/deregister", methods=["POST"])
def deregister():
    id = request.form.get("id")
    if id:
        db.execute("DELETE FROM registrants WHERE id = ?", id)
    return redirect("/registrants")

