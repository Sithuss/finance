from flask import Flask, request, render_template
import cs50

db = cs50.SQL("sqlite:///shows.db")

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search")
def search():
    shows = db.execute("SELECT * FROM shows where title like (?) LIMIT 50", "%" + request.args.get("q") + "%")
    return render_template("search.html", shows=shows)