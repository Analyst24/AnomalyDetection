from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one or log in.')

class UploadDatasetForm(FlaskForm):
    file = FileField('CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'CSV files only!')
    ])
    description = TextAreaField('Description')
    time_column = StringField('Time Column Name', validators=[DataRequired()])
    value_column = StringField('Energy Value Column Name', validators=[DataRequired()])
    submit = SubmitField('Upload')

class DetectionForm(FlaskForm):
    dataset = SelectField('Select Dataset', coerce=int, validators=[DataRequired()])
    algorithm = SelectField('Algorithm', choices=[
        ('isolation_forest', 'Isolation Forest'),
        ('autoencoder', 'AutoEncoder'),
        ('kmeans', 'K-Means Clustering')
    ], validators=[DataRequired()])
    submit = SubmitField('Run Detection')

class SettingsForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[Length(min=8, message="Password must be at least 8 characters")])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password', message="Passwords must match")])
    submit = SubmitField('Save Changes')
