import os
import secrets
from pathlib import Path
from urllib.parse import urlparse, unquote

import pyrebase
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, flash, session, redirect, request
from flask_restx import Api, Namespace, Resource, fields, reqparse
from flask_wtf import FlaskForm
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from wtforms import SubmitField, PasswordField, EmailField, StringField, IntegerField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, Length
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
storage = firebase.storage()


# Models
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cover_url = db.Column(db.String)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.Integer, nullable=False)
    publication_year = db.Column(db.Integer, nullable=False)
    main_genre = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __repr__(self):
        # return f'Title: {self.title} - Description: {self.description}'
        return f'ID: {self.id} - Title: {self.title}'


class ApiKey(db.Model):
    id_api = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    api_key = db.Column(db.String(64), nullable=False)
    requests_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())


# Forms
class LoginForm(FlaskForm):
    email = EmailField('Email: ', validators=[DataRequired(), Email()])
    password = PasswordField('Password: ', validators=[DataRequired()])
    submit = SubmitField('Sign in')


class RegisterForm(FlaskForm):
    email = EmailField('Email: ', validators=[DataRequired(), Email()])
    password = PasswordField('Password: ', validators=[DataRequired(), Length(min=6)])
    repeated_password = PasswordField('Repeat password: ', validators=[DataRequired()])
    submit = SubmitField('Register')


class BookForm(FlaskForm):
    cover = FileField('Cover image (optional)')
    title = StringField('Title', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    publication_year = IntegerField('Publication year', validators=[DataRequired()])
    main_genre = StringField('Main Genre', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Add')

    # @staticmethod
    # def validate_cover(form, field):
    #     if field.data:
    #         field.data = re.sub(r'[^a-z0-9_.-]', '_', field.data)


@app.route('/')
def index():
    if session.get('user'):
        api_key = ApiKey.query.filter_by(email=session['user']['email']).first().api_key
    else:
        api_key = 'Log in to see Your API key.'
    list_of_books = Book.query.order_by(Book.created_at)
    return render_template('index.html', list_of_books=list_of_books, api_key=api_key)


# Swagger (must be after '/' endpoint, so it won't steal its path)
api = Api(app, doc='/docs/')

ns = Namespace("books", description="Books desc")

api.add_namespace(ns)


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
            session['logged_in'] = True
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
            return redirect('/register')
        else:
            try:
                # Create account
                auth.create_user_with_email_and_password(email, password)
                flash('Registered successfully')
                # Log in to session
                session['logged_in'] = True
                session['user'] = auth.sign_in_with_email_and_password(email, password)
                # Create an API key for user
                generated_api_key = secrets.token_hex(32)
                api_key = ApiKey(email=session['user']['email'], api_key=generated_api_key, requests_count=0)
                db.session.add(api_key)
                db.session.commit()
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


def upload_and_get_file_url(cover: FileStorage) -> str:
    if cover == '':
        # Default image in the database
        img_url = os.getenv('DEFAULT_COVER_IMG')
    else:
        # Get file name and extension
        file_name, file_ext = os.path.splitext(secure_filename(cover.filename))
        # Generate unique number, so there is no duplicate images in the database
        unique_string = str(int(datetime.timestamp(datetime.utcnow())))
        # Unique file name
        file = file_name + unique_string + file_ext
        # Save temporarily for upload
        cover.save(os.path.join(app.instance_path, file))
        # Get downloadToken to get url for file in database
        keys = storage.child(f'images/{file}').put(file=f'instance/{file}', token=session['user']['idToken'])
        download_token = keys['downloadTokens']
        # Remove temp file after upload
        os.remove(f'{app.instance_path}/{file}')
        # Get url for uploaded image
        img_url = storage.child(f'images/{file}').get_url(download_token)

    return img_url


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if not session.get('logged_in'):
        flash('You need to be logged in to access this feature')
        return redirect('/')
    form = BookForm()
    if form.validate_on_submit():
        cover = form.cover.data
        img_url = upload_and_get_file_url(cover)

        book = Book(cover_url=img_url, title=form.title.data, author=form.author.data,
                    publication_year=form.publication_year.data,
                    main_genre=form.main_genre.data, description=form.description.data)
        db.session.add(book)
        db.session.commit()

        form.title.data = ''
        form.author.data = ''
        form.publication_year.data = None
        form.description.data = ''
        form.main_genre.data = ''
        form.cover.data = ''
        flash('Book Added Successfully')

    return render_template('add_book.html', form=form)


@app.route('/books/<book_title>-<id>')
def show_book(id, book_title):
    book = Book.query.get_or_404(id)
    return render_template('show_book.html', book=book)


def get_filename_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    decoded_path = unquote(parsed_url.path)
    filename = decoded_path.split('/')[-1]

    return filename


@app.route('/books/<book_title>-<id>/edit', methods=['GET', 'POST'])
def edit_book(id, book_title):
    book = Book.query.get_or_404(id)
    form = BookForm()
    if request.method == 'GET':
        form.description.data = book.description
    if form.validate_on_submit():
        cover = form.cover.data
        if cover.filename != '':
            url = book.cover_url
            # Get file name from url
            filename = get_filename_from_url(url)
            # Delete file from database
            storage.delete(f'images/{filename}', session['user']['idToken'])
            # Get url for new cover
            img_url = upload_and_get_file_url(cover)
        else:
            img_url = book.cover_url

        # Get fields data
        book.cover_url = img_url
        book.title = form.title.data
        book.author = form.author.data
        book.publication_year = form.publication_year.data
        book.main_genre = form.main_genre.data
        book.description = form.description.data

        # Update database
        db.session.add(book)
        db.session.commit()

        # Clear form fields
        form.title.data = ''
        form.author.data = None
        form.publication_year.data = None
        form.description.data = ''
        flash('Book updated')
        return redirect(f'/books/{book_title}-{id}')

    return render_template('edit_book.html', form=form, book=book)


@app.route('/books/<book_title>-<id>/download')
def download_book_cover(id, book_title):
    if not session.get('logged_in'):
        flash('You need to be logged in to access this feature')
        return redirect(f'/books/{book_title}-{id}')
    # Get book data
    book = Book.query.get_or_404(id)
    # Get cover's url
    url = book.cover_url
    filename = get_filename_from_url(url)
    # Path to Downloads folder
    downloads_path = str(Path.home() / "Downloads")
    # Download file
    storage.child(f'images/{filename}').download(path='', filename=f'{downloads_path}/{filename}',
                                                 token=session['user']['idToken'])
    flash('Successfully downloaded cover file! Check your Downloads folder.')

    return redirect(f'/books/{book_title}-{id}')


model_book = api.model('Book', {
    'title': fields.String(required=True, description='Book title'),
    'author': fields.String(required=True, description='Auther'),
    'cover_url': fields.String(description="Link for book's cover"),
    'publication_year': fields.Integer(required=True, description='Publication year'),
    'main_genre': fields.String(required=True, description='Main Genre'),
    'description': fields.String(required=True, description='Description'),
})

model_error_404 = api.model('Error', {
    'message': fields.String(description='Book not found')
})


def check_api_key(api_key: str):
    # Check if API key was given
    if api_key is None:
        return {'message': 'API key is missing'}
    # Check if API key is the database
    key = ApiKey.query.filter_by(api_key=api_key).first()
    if key is None:
        return {'message': 'wrong API key'}
    else:
        key.requests_count += 1
        db.session.add(key)
        db.session.commit()


# REST
@ns.route('')
@ns.param('api_key', 'Your API key')
@ns.response(404, 'Book not found', model=model_error_404)
class BooksShowAll(Resource):
    def get(self):
        # Validate API key
        api_key = request.args.get('api_key')
        check_api_key(api_key)

        books = Book.query.all()

        output = []
        for book in books:
            book_data = {'id': book.id, 'cover_url': book.cover_url, 'title': book.title, 'author': book.author,
                         'publication_year': book.publication_year, 'main_genre': book.main_genre,
                         'description': book.description, 'created_at': book.created_at.strftime('%Y-%m-%d %H:%M:%S')}

            output.append(book_data)

        return {'books': output}

    @ns.doc('todo')
    @ns.marshal_with(model_book, code=200)
    @ns.expect(model_book)
    def post(self):
        # Validate API key
        api_key = request.args.get('api_key')
        check_api_key(api_key)

        book = Book(cover_url=request.json['cover_url'],
                    title=request.json['title'],
                    author=request.json['author'],
                    publication_year=request.json['publication_year'],
                    main_genre=request.json['main_genre'],
                    description=request.json['description'])

        db.session.add(book)
        db.session.commit()
        return {'id': book.id, 'created_at': book.created_at}


@ns.route('/<id>')
@ns.response(404, 'Book not found')
@ns.param('id', 'book id')
@ns.param('api_key', 'Your API key')
class BookShowOne(Resource):
    def get(self, id):
        # Validate API key
        api_key = request.args.get('api_key')
        check_api_key(api_key)

        book = Book.query.get_or_404(id)
        return {'id': book.id, 'cover_url': book.cover_url, 'title': book.title, 'author': book.author,
                'publication_year': book.publication_year, 'main_genre': book.main_genre,
                'description': book.description, 'created_at': book.created_at.strftime('%Y-%m-%d %H:%M:%S')}

    @ns.marshal_with(model_book, code=200)
    @ns.expect(model_book)
    def put(self, id):
        # Validate API key
        api_key = request.args.get('api_key')
        check_api_key(api_key)

        book = Book.query.get_or_404(id)
        if book is None:
            return {'error': 'not found'}

        book.cover_url = request.json['cover_url']
        book.title = request.json['title']
        book.author = request.json['author']
        book.publication_year = request.json['publication_year']
        book.main_genre = request.json['main_genre']
        book.description = request.json['description']

        db.session.add(book)
        db.session.commit()

        return {'message': f'book: {book.id} updated'}

    def delete(self, id):
        # Validate API key
        api_key = request.args.get('api_key')
        check_api_key(api_key)

        book = Book.query.get(id)
        if book is None:
            return {'error': 'not found'}
        db.session.delete(book)
        db.session.commit()
        return {'message': 'book yeeeted'}


# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run()
