from flask import Flask
from urllib.parse import quote
from flask_sqlalchemy import SQLAlchemy
import cloudinary
from flask_login import LoginManager

app = Flask(__name__)
app.secret_key = 'SAJDABCABKDW%I%'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/studentdb?charset=utf8mb4" % quote('Admin@123')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config['PAGE_SIZE'] = 3

db = SQLAlchemy(app)

cloudinary.config(cloud_name='dz03d8gcs',
                  api_key='948214218945475',
                  api_secret='0P-i_6lF02Tx_5aV3RgJV_dZkbQ')

login = LoginManager(app=app)