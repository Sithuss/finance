from flask import Flask, request, render_template, redirect

SPORTS = ["baseball", "basketall", "batminton", "judo"]
app = Flask(__name__)

REGISTRANTS = {}

@app.route("/")
def index():
    return render_template("index.html", sports = SPORTS)

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    sport = request.form.get("sport")
    if not request.form.get("name") or request.form.get("sport") not in SPORTS:
        return render_template("falied_to_register.html")

    REGISTRANTS[name] = sport 

    return redirect("/registrants")

@app.route("/registrants")
def registrants():
    return render_template("registrants.html", registrants = REGISTRANTS)


    
