# config.py
import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'sisfamsandu@2005')

SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Sisfamsandu%402005@localhost/attendance_tracker'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Email (Gmail example) - you'll fill these later
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'vprajwal2204@gmail.com'
MAIL_PASSWORD = 'your_app_password'  # generate an app password for Gmail
ALERT_THRESHOLD = 75  # percent
