from flask import current_app
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, IntegerField, SubmitField, TextAreaField, URLField, PasswordField
from wtforms.validators import InputRequired, NumberRange, Email, Length, EqualTo, ValidationError
from datetime import datetime

current_year = int(datetime.now().year)


class MovieForm(FlaskForm):
    title = StringField(
        label="Title",
        validators=[InputRequired(message="Add a valid movie title")]
    )

    director = StringField(
        label="Director",
        validators=[InputRequired(message="Please specify the director of the movie title!")]
    )

    year = IntegerField(
        label="Year of production",
        validators=[InputRequired(message="What year?"),
                    NumberRange(min=1900, max=current_year, message=f"Year must be between 1900 and {current_year}")]
    )

    submit = SubmitField(label="Add a movie")


class StringListField(TextAreaField):
    def _value(self):
        if self.data:
            return "\n".join(self.data)
        else:
            return ""

    def process_formdata(self, valuelist):
        # checks valuelist contains at least 1 element, and the first element isn't falsy (i.e. empty string)
        if valuelist and valuelist[0]:
            self.data = [line.strip() for line in valuelist[0].split("\n")]
        else:
            self.data = []


class ExtendedMovieForm(MovieForm):
    cast = StringListField(label="Cast")
    series = StringListField(label="Series")
    tags = StringListField(label="Tags")
    description = TextAreaField(label="Description")
    video_link = URLField(label="Video Link")

    submit = SubmitField("Submit")


# WTForm register
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField('Password',
                             validators=[InputRequired(),
                                         Length(min=8, message="Password should be at least 8 characters")])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[InputRequired(),
                                                 EqualTo("password",
                                                         message="Password did not match!")])
    name = StringField("Name", validators=[InputRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField("Sign me up!")

    def validate_email(self, email):
        """Note that we are not calling the validate_email method directly in the register function anymore. Instead,
        we have defined it as a validator for the email field in the RegisterForm class. This means that when
        form.validate_on_submit() is called, the validate_email method will be automatically called for the email
        field as well. If the validate_email method raises a ValidationError, it will be displayed as an error
        message in the form."""
        user_check = current_app.db.users.find_one({"email": email.data})
        if user_check:
            raise ValidationError("This email address is already registered.")


# WTForm register
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField("Login")
