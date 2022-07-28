import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_data = db.execute("SELECT symbol, sum(shares) FROM activity WHERE a_id = ? GROUP BY symbol", session["user_id"])

    total = 0

    # iterate each stock and addiong additional key:value pairs
    for d in user_data:
        dat = lookup(d["symbol"])
        com_name = dat["name"]
        stock_price = dat["price"]
        d["name"] = com_name
        d["price"] = stock_price
        d["total"] = stock_price * d["sum(shares)"]
        total = total + d["total"]

    user_cash = db.execute("SELECT cash FROM users where id = ?", session["user_id"])
    cash = user_cash[0]["cash"]
    # accountind total cash that user has
    all = round(cash + total, 2)

    return render_template("index.html", data=user_data, cash=cash, total=all)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # get symbol
        buy = request.form.get("symbol")
        # varifying the symbol
        if not buy:
            return apology("MISSING SYMBOL", 400)
        # getting shares
        shares = request.form.get("shares")
        if not shares:
            return apology("missing shares", 400)

        buy_data = lookup(buy)
        if buy_data == None:
            return apology("INVALID SYMBOL", 400)
        # change shares into int type if input is integer
        try:
            shares = int(shares)
        except ValueError:
            return apology("invalid shares", 400)
        # chack valid amount
        if shares <= 0:
            print("hello")
            return apology("invalid shares", 400)

        stock_price = buy_data["price"]
        stock_symbol = buy_data["symbol"]
        # extract user's current cash
        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        user_current_cash = user[0]["cash"]

        multiplier = shares * stock_price

        if multiplier > user_current_cash:
            return apology("can't afford", 400)

        new_cash = user_current_cash - multiplier
        # adding data into database
        db.execute("UPDATE users SET cash = ? WHERE id = ?", round(new_cash, 2), session["user_id"])

        db.execute("INSERT INTO activity (a_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
                   session["user_id"], stock_symbol, shares, stock_price)

        return redirect("/")
    # if menthod == get, go render_template
    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    data = db.execute("SELECT * FROM activity WHERE a_id = ? ORDER BY dt", session["user_id"])

    return render_template("history.html", user_data=data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        name = rows[0]["username"]

        flash(f"You are logged in as {name}.")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        # get symbol
        symbols = request.form.get("symbol")
        data = lookup(symbols)

        if data == None:
            return apology("INVALID SYMBOL", 400)
        # go to quoted.html
        return render_template("quoted.html", data=data)
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")
        # check condition if username is bloak or alerady exixts in database
        db_name = db.execute("SELECT username FROM users")
        used_name = [d['username'] for d in db_name]

        if not username:
            return apology("Username not available", 400)

        elif username in used_name:
            return apology("Username exits")

        elif not password:
            return apology("missing password")

        elif password != confirm:
            return apology("password didn't match")
        # making password with by hashing
        hash_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash_password)

        return redirect("/login")

    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    data = db.execute("SELECT * FROM activity WHERE a_id = ? GROUP BY symbol", session["user_id"])
    symbols = []
    for d in data:
        sym = d["symbol"]
        symbols.append(sym)

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol:
            return apology("missing symbol", 400)

        elif not shares:
            return apology("missing shares", 400)

        get_data = lookup(symbol)
        price = get_data["price"]
        ggshares = int(shares)
        multiplier = price * ggshares

        db_shares = db.execute("SELECT SUM(shares) FROM activity WHERE a_id = ? AND symbol = ?", session["user_id"], symbol)
        total_shares = db_shares[0]["SUM(shares)"]

        if ggshares > total_shares:
            return apology("too many shares", 400)

        cash_data = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        user_cash = cash_data[0]["cash"]
        new_cash = user_cash + multiplier
        print(new_cash)

        db.execute("INSERT INTO activity (a_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
                   session["user_id"], symbol, -ggshares, price)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, session["user_id"])

        return redirect("/")

    return render_template("sell.html", symbols=symbols)


@app.route("/change_name", methods=["GET", "POST"])
@login_required
def change_name():
    """Change username"""
    if request.method == "POST":
        name = request.form.get("name")

        if not name:
            return apology("user name not available", 400)

        db_name = db.execute("SELECT username FROM users")
        used_name = [d["username"] for d in db_name]

        if name in used_name:
            return apology("username already used", 400)
        db.execute("UPDATE users set username = ? WHERE id = ?", name, session["user_id"])

        flash(f"Name changed to {name}.")
        return redirect("/")
    return render_template("name_change.html")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """change user password"""
    if request.method == "POST":
        current_password = request.form.get("current_password")

        rows = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])

        if not check_password_hash(rows[0]["hash"], current_password):
            return apology("current password worng")

        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        if not new_password:
            return apology("missing new password")
        elif not confirmation:
            return apology("missing re-type")
        elif new_password != confirmation:
            return apology("passwords didn't match")

        new_hash_password = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=8)
        db.execute("UPDATE users SET hash = ? WHERE id =?", new_hash_password, session["user_id"])

        flash("New password updated!")
        return redirect("/")
    return render_template("change_password.html")


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete_account():
    """delete account"""
    if request.method == "POST":
        delete = request.form.get("delete")
        if not delete:
            return redirect("/delete")

        confirm = "I want to delete my account"

        if delete != confirm:
            return redirect("/delete")

        db.execute("DELETE FROM activity WHERE a_id = ?", session["user_id"])
        db.execute("DELETE FROM users WHERE id = ?", session["user_id"])

        session.clear()
        return redirect("/")
    return render_template("delete.html")