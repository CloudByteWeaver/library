import os
import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    yield client


@pytest.fixture
def login(client):
    form_data = {
        'email': 'konrad.janiszewski.us@gmail.com',
        'password': 'tajneHaslo123'
    }
    client.post('/login', data=form_data)
