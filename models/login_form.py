from wtforms import SubmitField, StringField, PasswordField, validators
from flask_wtf import FlaskForm

class LoginForm(FlaskForm): 
    usernameOrEmail = StringField('Username', [validators.DataRequired()])

    password = PasswordField('Password', [validators.DataRequired()])  

    submit = SubmitField('Submit')