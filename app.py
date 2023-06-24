import os
import pyrebase
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, flash, session, redirect
from flask_wtf import FlaskForm
from wtforms import SubmitField, PasswordField, EmailField, StringField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email
from flask_sqlalchemy import SQLAlchemy

load_dotenv('.env')

app = Flask(__name__)

# Add database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
# Secret key
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# Initialize database
db = SQLAlchemy(app)


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
# storage = firebase.storage()
# user = auth.sign_in_with_email_and_password('konrad.janiszewski.us@gmail.com', 'tajneHaslo123')
# storage.child('test.txt').download(path='', filename='C:/Users/Konrad/Desktop/Projekty/Test/downloaded.txt', token=user['idToken'])
# storage.child('test.jpg').put('C:/Users/Konrad/Desktop/Projekty/Test/test.jpg')


# Models
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    id_author = db.Column(db.Integer, nullable=False)
    publication_year = db.Column(db.Integer, nullable=False)
    main_genre = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __repr__(self):
        return f'Title: {self.title} - Description: {self.description}'


# class Author(db.Model):
#     id_author = db.Column(db.Integer, primary_key=True)
#     first_name = db.Column(db.String(25), nullable=False)
#     last_name = db.Column(db.String(50), nullable=False)
#     about = db.Column(db.String, nullable=False)
#
#     def __repr__(self):
#         return '<Last name: %r>' % self.last_name


# Forms
class LoginForm(FlaskForm):
    email = EmailField('Email: ', validators=[DataRequired(), Email()])
    password = PasswordField('Password: ', validators=[DataRequired()])
    submit = SubmitField('Sign in')


class RegisterForm(FlaskForm):
    email = EmailField('Email: ', validators=[DataRequired(), Email()])
    password = PasswordField('Password: ', validators=[DataRequired()])
    repeated_password = PasswordField('Repeat password: ', validators=[DataRequired()])
    submit = SubmitField('Register')


class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    id_author = IntegerField('Author', validators=[DataRequired()])
    publication_year = IntegerField('Publication year', validators=[DataRequired()])
    main_genre = StringField('Main Genre', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Add')


@app.route('/')
def index():
    list_of_books = Book.query.order_by(Book.created_at)
    return render_template('index.html', list_of_books=list_of_books)


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


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    form = BookForm()
    if form.validate_on_submit():
        # book = Book.query.filter_by(email=form.email.data).first()
        book = Book(title=form.title.data, id_author=form.id_author.data, publication_year=form.publication_year.data,
                    main_genre=form.main_genre.data, description=form.description.data)
        db.session.add(book)
        db.session.commit()

        form.title.data = ''
        form.id_author.data = None
        form.publication_year.data = None
        form.description.data = ''
        flash('Book Added Successfully')

    return render_template('add_book.html', form=form)


@app.route('/books/<id>', methods=['DELETE'])
def delete_book(id):
    book = Book.query.get(id)
    if book is None:
        return {'error': 'not found'}
    db.session.delete(book)
    db.session.commit()
    return {'message': 'yeeet'}


@app.route('/books')
def get_books():
    books = Book.query.all()

    output = []
    for book in books:
        book_data = {'id': book.id, 'title': book.title, 'id_author': book.id_author,
                     'publication_year': book.publication_year, 'main_genre': book.main_genre,
                     'description': book.description, 'created_at': book.created_at}

        output.append(book_data)

    return {'books': output}


@app.route('/books/<id>')
def get_book(id):
    book = Book.query.get_or_404(id)
    return {'id': book.id, 'title': book.title, 'id_author': book.id_author,
            'publication_year': book.publication_year, 'main_genre': book.main_genre,
            'description': book.description, 'created_at': book.created_at}


# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run()
