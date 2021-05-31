from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from sender import email_sequence
import sqlite3
import re
import hashlib
import hmac
import pytz
import datetime
from events import main
from extraFunctions import login_required, create_hash
from datetime import date

# Make an instance of a Flask app
app = Flask(__name__)

# Configure the app
# https://flask-session.readthedocs.io/en/latest/
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_FILE_THRESHOLD"] = 400
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = mkdtemp()
Session(app)

# Function that changes a variable stored in the database so it acts as a global variable
def set_variables(name, quantity):
    connection = sqlite3.connect("consultorio.db")
    db = connection.cursor()
    dbInfo = db.execute("UPDATE flask_variables SET value=? WHERE variable=?", (name, "edit_name"))
    dbInfo = db.execute("UPDATE flask_variables SET value=? WHERE variable=?", (quantity, "edit_quantity"))
    connection.commit()
    # closing the connection to prevent any data leaks or over congestion of the connections
    connection.close()

# Retrives the variable name/id from the database
def get_name():
    connection = sqlite3.connect("consultorio.db")
    db = connection.cursor()
    dbInfo = db.execute("SELECT value FROM flask_variables WHERE variable=?", ("edit_name",)).fetchall()
    return dbInfo[0][0]

# Retrives the variable quantity from the database
def get_quantity():
    connection = sqlite3.connect("consultorio.db")
    db = connection.cursor()
    dbInfo = db.execute("SELECT value FROM flask_variables WHERE variable=?", ("edit_quantity",)).fetchall()
    return dbInfo[0][0]

#https://flask.palletsprojects.com/en/2.0.x/api/
@app.after_request
def after_request(response):
    response.headers["Expires"] = 0
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Pragma"] = "no-cache"
    return response

# Handling the "/" route which is the main page
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # Handlig if the request method is POST or GET
    # POST allows to insert a new patient into the database
    if request.method == "POST":
        # Get the variables from the form
        name = request.form.get("name")
        quantity = request.form.get("quantity")
        # If any of the values are empty an error message if flashed
        if(name == "" or quantity == ""):
            flash("Llene todos los espacios")
            return redirect("/")
        else:
            # Getting the currency selected, either MXN or USD
            currency = request.form.get("currency")
            # Make the connection to the database
            connection = sqlite3.connect("consultorio.db")
            db = connection.cursor()
            # Insert the data to the correct headings and table
            dbInfo = db.execute("INSERT INTO currentItems(name, quantity, currency) VALUES(?,?,?)", (name, quantity, currency))
            # Save the changes
            connection.commit()
            # closing the connection to prevent any data leaks or over congestion of the connections
            connection.close()
            return redirect("/")
    else:
        # Connect to the database and select all the active items to display them
        connection = sqlite3.connect("consultorio.db")
        db = connection.cursor()
        dbInfo = db.execute("SELECT * FROM currentItems").fetchall()
        # closing the connection to prevent any data leaks or over congestion of the connections
        connection.close()
        # Render the main page with the items selected to display them
        return render_template("consultas.html", items=dbInfo)

# Handling the "/current" route which is the same as "/" but for a specific user
@app.route("/current", methods=["GET"])
@login_required
def current():
    # Get today's date in my timezone to avoid errors
    today = datetime.datetime.now(pytz.timezone('America/Monterrey'))
    # Format the string so it only shows the date and not the time
    currentDate = today.strftime("%Y-%m-%d")
    # Connect to the database
    connection = sqlite3.connect("consultorio.db")
    db = connection.cursor()
    # Select all of the current patients if they have been registered
    dbInfo = db.execute("SELECT * FROM history WHERE date=?",(currentDate,)).fetchall()

    if(len(dbInfo) != 0):
        # Initialize the variables
        totalMX = 0
        totalUSD = 0
        # Iterate over the items to make the sum of USD and MXN
        for item in dbInfo:
            if(item[3] == "MXN"):
                totalMX += item[2]
            else:
                totalUSD += item[2]
        # Return the template with the necessary information to show the specific user the information
        return render_template("consultashoy.html", items=dbInfo, totalMxn=f"${totalMX:,.2f}", totalUsd=f"${totalUSD:,.2f}")
    else:
        # If there's no result an error message is shown
        flash("No se han timbrado citas el día de hoy")
    connection.close()
    return render_template("consultashoy.html")

# Handling the "/login" route which allows the users to login
@app.route("/login", methods=["GET", "POST"])
def login():
    # Handling the POST method
    if request.method == "POST":
        # Clear the past user so there's no connection between them
        session.clear()
        # Get the values issued in the form
        # Make the username UPPERCASE to eliminate case sensitivity
        username = request.form.get("username1").upper()
        inserted_password = request.form.get("password")
        # If there's an empty input, an error gets flashed
        if(username == "" or inserted_password == ""):
            flash("Espacios no llenados")
        else:
            # Connect to the database
            connection = sqlite3.connect("consultorio.db")
            db = connection.cursor()
            # Select the username from the database
            dbInfo = db.execute("SELECT * FROM users WHERE UPPER(username)=?", (username,)).fetchall()
            # If there's no results, an error get's flashed
            if(len(dbInfo) == 0):
                flash("Usuario no existe")
            else:
                # If the hashed version of the inserted password matches the stored hashed password the user get's logged in
                if(create_hash(inserted_password) == dbInfo[0][2]):
                    # Store the current session id with the user's database id
                    session["user_id"] = (dbInfo[0])[0]
                    # If the user is the dentist, redirect to "/current"
                    if(session["user_id"] == 1):
                        return redirect("/current")
                    # Else if the user is the assistant, it gets redirected to "/"
                    else:
                        # Retrieve the checklist from the database to check if the emails have been sent for the day or not
                        checklist = db.execute("SELECT * FROM checklist").fetchall()
                        # Retrieve's today's date from my specific timezone
                        today = datetime.datetime.now(pytz.timezone('America/Monterrey'))
                        # Format the string to only include the date and not the time
                        todayDate = today.strftime("%Y-%m-%d")
                        # If the checklist doesn't match today's date
                        if (checklist[0][1] != str(todayDate) and checklist[0][2] == 1):
                            # The main from the events.py get's executed to send the emails
                            main()
                            # The previous checklist gets deleted
                            db.execute("DELETE FROM checklist")
                            # A new line is inserted into the checklist with today's date
                            db.execute("INSERT INTO checklist(date, checker) VALUES(?, ?)", (str(todayDate), 1))
                            # Saves the changes
                            connection.commit()
                            # Flash a message to show that the emails have been sent
                            flash("Recordatorios Enviados")
                        return redirect("/")
                else:
                    # If the password doesn't match, a message get's flashed that it's incorrect
                    flash("Contraseña incorrecta")
                    return redirect("/")
            # Close the connection to prevent errors
            connection.close()
        return redirect("/")
    else:
        # Redirect to the main login page
        return render_template("login.html")

# Handling the "/submit" route which allows to dump the date into the history database
@app.route("/submit", methods=["POST"])
@login_required
def submit():
    # Handles POST request
    if request.method == "POST":
        # Connect to the database
        connection = sqlite3.connect("consultorio.db")
        db = connection.cursor()
        # Select all the currently active items
        dbInfo = db.execute("SELECT * FROM currentItems").fetchall()
        # If there are items in the list proceed
        if(len(dbInfo) != 0):
            # Get today's date in my current time zone
            today = datetime.datetime.now(pytz.timezone('America/Monterrey'))
            # Format the date to only show the date and not the time
            currentDate = today.strftime("%Y-%m-%d")
            # For each item, insert it into the history table in the database
            for item in dbInfo:
                db.execute("INSERT INTO history(name, quantity, currency, date) VALUES(?,?,?, ?)", (item[1], item[2], item[3], currentDate))
            # Clear the current items table to start from a new fresh start
            db.execute("DELETE FROM currentItems")
            # Save the changes
            connection.commit()
        else:
            # Else flash an error message to let know that nothing is registered
            flash("No hay consultas registradas")
        # Close the connection to prevent any errors
        connection.close()
        # Redirect the user to the main page
        return redirect("/")

# Handling the "/edit" route which allows to edit the information of an item while it hasn't been submitted to the history table
@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    # Handle the POST request
    if request.method == "POST":
        # Retrive the form data
        new_name = request.form.get('name')
        new_quantity = request.form.get('quantity')
        new_currency = request.form.get('currency')
        # Connect the database
        connection = sqlite3.connect("consultorio.db")
        db = connection.cursor()
        # Update the database with the current items to the new information
        dbInfo = db.execute("UPDATE currentItems SET name=?, quantity=?, currency=? WHERE id=? AND quantity=?", (new_name, new_quantity, new_currency, get_name(), get_quantity()))
        # Save the changes
        connection.commit()
        # Close the connection to prevent any errors
        connection.close()
        # Redirect the user to the main page with the new data
        return redirect("/")
    else:
        # Retrive the data
        data = request.args.get('edit_button')
        # Split the data in the "-" which includes the user's id from the table and the price as identification method
        data = data.split('-')
        # Set the "global" variables to use in the post method
        set_variables(str(data[0]), str(data[1]))
        # Connect the database
        connection = sqlite3.connect("consultorio.db")
        db = connection.cursor()
        # Selects the current user from the active items
        dbInfo = db.execute("SELECT * FROM currentItems WHERE id=? AND quantity=?", (data[0], data[1])).fetchall()
        # Close the connection to prevent errors
        connection.close()
        # If the currency is now  MXN or USD is checked to preselect that radiobutton for the user
        if str(dbInfo[0][3]) == "MXN":
            boolUsd = ''
            boolMx = 'checked="checked"'
        else:
            boolUsd = 'checked="checked"'
            boolMx = ''
        # Return the template with the data from the selected user
        return render_template("edit.html", boolUsd=boolUsd, boolMx=boolMx, bName=dbInfo[0][1], bQuantity=dbInfo[0][2])

# Handling the "/logout" route which allows a user to logout of the app
@app.route("/logout")
def logout():
    # Forget the previous session
    session.clear()
    # Redirect to the main page which should load the login page
    return redirect("/")

# Handling the "/history" route which allows to lookup the history of the payments
@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    # Handling the post request
    if request.method == "POST":
        # If the search type is N for name continue with the next
        if request.form.get("search-type") == "N":
            # Retrive the data
            name = request.form.get("name")
            # If the name is not empty continue
            if (name != ""):
                # Format the string to seach any like data in the database
                name = "%" + name.upper() + "%"
                # Connect to the database
                connection = sqlite3.connect("consultorio.db")
                db = connection.cursor()
                # Select all of the data searching by name
                dbInfo = db.execute("SELECT * FROM history WHERE UPPER(name) LIKE ?", (name,)).fetchall()
                # Close the connection to prevent any errors
                connection.close()
                # If there's information render the template with the found information
                if len(dbInfo) !=0:
                    return render_template("history.html", items=dbInfo)
                else:
                    # Else if it's empty flash an error
                    flash("No hay datos con ese nombre")
            else:
                # Else if it's empty flash an error
                flash("Llene los datos")
        # If the search type is D for date continue with the next
        else:
            date = request.form.get("date")
            if date != "":
                # Connect to the database
                connection = sqlite3.connect("consultorio.db")
                db = connection.cursor()
                # Select all of the data searching by date
                dbInfo = db.execute("SELECT * FROM history WHERE date=?", (date,)).fetchall()
                # Close the connection to prevent any errors
                connection.close()
                # If there's information render the template with the information found
                if len(dbInfo) !=0:
                    return render_template("history.html", items=dbInfo)
                else:
                    # Else if it's empty flash an error
                    flash("No hay datos en esta fecha")
            else:
                # Else if it's empty flash an error
                flash("Llene los datos")
        return redirect("/history")
    else:
        # Else return the history template with no data
        return render_template("history.html")

# Handling the "/calendar" route which allows to send a remainder using the API's
@app.route("/calendar", methods=["GET", "POST"])
@login_required
def calendar():
    # Handle the POST request
    if request.method == "POST":
        # Retrive the data
        a_mail = request.form.get("mail")
        a_date = request.form.get("date")
        a_time = request.form.get("time")
        # If any of the data id empty
        if (a_mail == "" or a_date == "" or a_time == ""):
            # Flash a message with the errors
            flash("Llene todos los datos")
        else:
            # Strip the string just to prevent any error mistakes
            a_mail = str(a_mail).strip()
            # Send the data to the email sequence of sender.py to send the email
            email_sequence(a_mail, a_time, a_date)
            # Flash a message to show that it has been sent
            flash("Recordatorio Enviado")
        # Return to "/calendar"
        return redirect("/calendar")
    else:
        # Return the template of calendar.html
        return render_template("calendar.html")
