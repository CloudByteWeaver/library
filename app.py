import os
from abc import ABC

from dotenv import load_dotenv
from firebase_admin import credentials
from flask import Flask, render_template, flash, session, redirect
from flask_firebase_admin import FirebaseAdmin
from flask_wtf import FlaskForm
from wtforms import SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, Email
import pyrebase

load_dotenv('.env')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
firebase_config = {
    "apiKey": os.getenv('API_KEY'),
    "authDomain": os.getenv('AUTH_DOMAIN'),
    "projectId": os.getenv('PROJECT_ID'),
    "databaseURL": os.getenv('DATABASE_URL'),
    "storageBucket": os.getenv('STORAGE_BUCKET'),
    "messagingSenderId": os.getenv('MESSAGING_SENDER_ID'),
    "appId": os.getenv('APP_ID'),
    "serviceAccount": os.getenv('SERVICE_ACCOUNT')
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()


# app.config['FIREBASE_ADMIN_CREDENTIAL'] = credentials.Certificate('paw-1-5a796-firebase-adminsdk-4x8yo-5e71fdd6ba.json')
# firebase = FirebaseAdmin(app)

class LoginForm(FlaskForm):
    email = EmailField('Email: ', validators=[DataRequired(), Email()])
    password = PasswordField('Password: ', validators=[DataRequired()])
    submit = SubmitField('Sign in')


class RegisterForm(FlaskForm):
    email = EmailField('Email: ', validators=[DataRequired(), Email()])
    password = PasswordField('Password: ', validators=[DataRequired()])
    repeated_password = PasswordField('Repeat password: ', validators=[DataRequired()])
    submit = SubmitField('Register')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    email = None
    password = None
    form = LoginForm()
    alert_type = 'alert-danger'
    # Validate form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        form.email.data = ''
        form.password.data = ''
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            flash('Signed in successfully')
            alert_type = 'alert-success'
            session['isSigned'] = True
            session['user'] = user
        except Exception as e:
            flash('Oops! Please check the email address or password you entered and try again.')
            print(e)

    return render_template('login.html',
                           email=email,
                           password=password,
                           form=form,
                           alert_type=alert_type)


@app.route('/register', methods=['GET', 'POST'])
def register():
    email = None
    password = None
    repeated_password = None
    form = RegisterForm()
    # Validate form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        repeated_password = form.repeated_password.data
        form.email.data = ''
        form.password.data = ''
        form.repeated_password = ''

        if password != repeated_password:
            flash('Error: The repeated password does not match the original password. Please make sure to enter the '
                  'same password in both fields.')
            print('różne')
            print(f'1: {password}')
            print(f'2: {repeated_password}')
            return redirect('/register')
        else:
            print('takie same')
            try:
                auth.create_user_with_email_and_password(email, password)
                flash('Registered successfully')
                session['isSigned'] = True
            except Exception as e:
                flash('Please check the password you entered and try again.')
                print(e)

    return render_template('register.html',
                           email=email,
                           password=password,
                           repeated_password=repeated_password,
                           form=form)


@app.route('/logout')
def logout():
    # session.clear()
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run()
