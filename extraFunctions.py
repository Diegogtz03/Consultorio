from flask import redirect, render_template, request, session
from functools import wraps
import hashlib
import datetime

# Flask function to make sure the user is logged in
def login_required(f):
    # https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# function that creates a hash of a password in order to compare it
def create_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()
