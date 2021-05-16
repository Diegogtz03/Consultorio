from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
import sqlite3
from extraFunctions import login_required

app = Flask(__name__)
# db = sqlite3.connect("")

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return redirect("/")
    else: 
        return render_template("login.html")

@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    if request.method == "POST":
        return redirect("historied.html")
    else: 
        return render_template("history.html")
        

@app.route("/calendar", methods=["GET", "POST"])
@login_required
def calendar():
    if request.method == ""