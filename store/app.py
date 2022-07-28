import cs50
from flask import Flask, redirect, render_template, request, session
from flask_session import Session

db = cs50.SQL("sqlite:///store.db")

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def index():
    books = db.execute("SELECT * FROM books")
    return render_template("books.html", books=books)

@app.route("/card", methods=["GET", "POST"])
def card():
    if "card" not in session:
        session["card"] = []

    if request.method == "POST":
        id = request.form.get("id")
        if id:
            session["card"].append(id)
        return redirect("/card")

    books = db.execute("SELECT * FROM books WHERE id in (?)", session["card"])
    return render_template("card.html", books=books)