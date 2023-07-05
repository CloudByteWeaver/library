import os
import pytest
from flask import session
from werkzeug.datastructures import FileStorage

from app import app, db, Book, auth


def test_index(client):
    response = client.get('/')
    assert response.status_code == 200


def test_login(client):
    response = client.get('/login')
    assert response.status_code == 200

    form_data = {
        'email': 'konrad.janiszewski.us@gmail.com',
        'password': 'tajneHaslo123'
    }

    response = client.post('/login', data=form_data)
    assert response.status_code == 200
    assert b'Signed in successfully' in response.data


def test_register(client):
    response = client.get('/register')
    assert response.status_code == 200

    form_data = {
        'email': 'example@gmail.com',
        'password': 'passwd123',
        'repeated_password': 'passwd123'
    }

    response = client.post('/register', data=form_data)
    assert response.status_code == 200
    assert b'Registered successfully' in response.data

    user = auth.sign_in_with_email_and_password('example@gmail.com', 'passwd123')
    auth.delete_user_account(user['idToken'])


def test_add_book(client):
    form_data = {
        'email': 'konrad.janiszewski.us@gmail.com',
        'password': 'tajneHaslo123'
    }
    response = client.post('/login', data=form_data)
    assert response.status_code == 200

    book = {
        'cover': FileStorage(filename=None),
        'title': 'Book test',
        'author': 'Author of the tested book',
        'publication_year': 2021,
        'main_genre': 'Fiction',
        'description': 'Description of the tested book'
    }

    response = client.post('/add_book', data=book)
    assert response.status_code == 200
    assert b'Book Added Successfully' in response.data

    with app.app_context():
        book = Book.query.filter_by(title='Book test').first()
        assert book is not None

    client.delete(f'/books/{book.id}?api_key=affb75e6521b97adeaf7b1a1dea9ea5933f03220e06d802ffe9386a618c3a6c5')


def test_delete_book(client):
    form_data = {
        'email': 'konrad.janiszewski.us@gmail.com',
        'password': 'tajneHaslo123'
    }
    response = client.post('/login', data=form_data)
    assert response.status_code == 200

    book = {
        'cover': FileStorage(filename=None),
        'title': 'Book test',
        'author': 'Author of the tested book',
        'publication_year': 2021,
        'main_genre': 'Fiction',
        'description': 'Description of the tested book'
    }
    response = client.post('/add_book', data=book)
    assert response.status_code == 200
    assert b'Book Added Successfully' in response.data

    with app.app_context():
        book = Book.query.filter_by(title='Book test').first()
        assert book is not None

        client.delete(f'/books/{book.id}?api_key=affb75e6521b97adeaf7b1a1dea9ea5933f03220e06d802ffe9386a618c3a6c5')
        book = Book.query.filter_by(title='Book test').first()
        assert book is None
