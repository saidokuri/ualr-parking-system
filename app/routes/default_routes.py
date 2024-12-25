from flask import render_template
from app import app
# from app.models.supervisor import Supervisor
from flask import redirect, url_for, session
from datetime import datetime




@app.route('/')
def index():
    
    return render_template('index.html' ,current_year=datetime.now().year)


