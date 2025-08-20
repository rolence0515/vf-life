import os
from datetime import timedelta

class Config:
    def __init__(self):
        self.APP_ENV = os.environ.get("APP_ENV", "uat").lower()
        self.DB_HOST = os.environ.get('DB_HOST', '34.96.232.148')  # 預設為公開IP
        self.DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Test123456!')
        self.DB_PORT = os.environ.get('DB_PORT', '5432')
        self.DB_USER = os.environ.get('DB_USER', 'postgres')
        self.DB_NAME = os.environ.get('DB_NAME', 'postgres')
        self.ADMIN_USERNAME = 'user'
        self.ADMIN_PASSWORD = '123456'
        self.ADMIN_USER_ID = 1
        self.SESSION_TIMEOUT_SECONDS = 3600  # Set session timeout to 1 hour
        self.REMEMBER_ME_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # Set 'Remember Me' cookie max age to 7 days
        self.WEBSITE_DOMAIN = os.environ.get('WEBSITE_DOMAIN', 'http://127.0.0.1:8080')

        # Email configuration for password recovery
        self.EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        self.EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 465))
        self.EMAIL_USER = os.environ.get('EMAIL_USER', 'activity@violetflames.com')
        self.EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'xfhx ovkq fftk xrwa')

        # Google reCAPTCHA 設定
        self.RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '')
        self.RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '')

# Create a single instance of Config
config = Config()