from wtforms import SubmitField, BooleanField, StringField, PasswordField, validators, ValidationError
from flask_wtf import FlaskForm

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def userExistsCheck(form, field):
    existentUser = db.execute("SELECT * FROM users WHERE username = :username OR email = :email", 
        {"username":field.data, "email":field.data}).fetchone()

    if existentUser:
        raise ValidationError('User already exists')

class RegistrationForm(FlaskForm):
    firstName = StringField('First Name', [validators.DataRequired()]) 

    lastName = StringField('Last Name', [validators.DataRequired()])   

    username = StringField('Username', [validators.DataRequired(), userExistsCheck]) 

    email = StringField('Email', [
        userExistsCheck,
        validators.DataRequired(), 
        validators.Email(), 
        validators.Length(min=6, max=35)
        ])

    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
        ])  

    confirm = PasswordField('Confirm Password', [validators.DataRequired()])
    
    submit = SubmitField('Submit')