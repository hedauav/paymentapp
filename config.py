import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_for_development')
    DATABASE = os.path.join(os.path.dirname(__file__), 'payment_app.db')
    DEBUG = True