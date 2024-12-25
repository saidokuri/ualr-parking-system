from flask import Flask, session
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
import os
import certifi
from flask_cors import CORS




app = Flask(__name__, static_folder='../static', static_url_path='/static')


app.config["MONGO_URI"] = "mongodb://localhost:27017/ualr-parking"
# app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.debug = True
app.secret_key = 'parking'
ca = certifi.where()

CORS(app)  




mongo = PyMongo(app)


