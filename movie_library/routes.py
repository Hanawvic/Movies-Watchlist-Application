import functools
import uuid
from dataclasses import asdict

from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app, abort
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import check_password_hash, generate_password_hash

from movie_library import mail, Config
from movie_library.forms import MovieForm, ExtendedMovieForm, RegisterForm, LoginForm
from movie_library.models import Movie, current_day, current_year, User

pages = Blueprint(
    "pages", __name__, template_folder="templates", static_folder="static"
)


# creating login required decorator
def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args, **kwargs):
        if not session.get("email"):
            return redirect(url_for(".login"))
        return route(*args, **kwargs)

    return route_wrapper


@pages.context_processor
def inject_current_year():
    return {"year": current_year}


# Serializer for token generation
serializer = URLSafeTimedSerializer(Config.SECRET_KEY)


@pages.route("/register", methods=["GET", "POST"])
def register():
    if session.get("email"):
        return redirect(url_for(".index"))

    form = RegisterForm()
    if form.validate_on_submit():
        # hash and salt password
        hash_and_salted_password = generate_password_hash(password=form.password.data, method="pbkdf2:sha256",
                                                          salt_length=8)
        new_user = User(
            _id=uuid.uuid4().hex,
            name=form.name.data,
            email=form.email.data,
            password=hash_and_salted_password,
        )

        # add new user to db
        current_app.db.users.insert_one(asdict(new_user))

        token = serializer.dumps(new_user.email, salt='email-confirm')

        # Send email confirmation to user
        confirmation_url = url_for('pages.confirm_email', token=token, _external=True)
        html = render_template('email_confirmation.html', user_name=new_user.name, confirmation_url=confirmation_url)
        msg = Message("Confirm Your Email Address", recipients=[new_user.email], html=html)
        mail.send(msg)

        flash(message=f"A confirmation email has been sent to {new_user.email}", category="success")
        return redirect(url_for(".register"))

    return render_template("register.html", form=form, title="Movies Watchlist - Register")


@pages.route('/confirm_email/<token>')
def confirm_email(token):
    """Returns the url that take the user to the login page to confirm his registration and update user confirm to
    True"""
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
        requested_user = current_app.db.users.find_one({"email": email})
        if requested_user:
            requested_user["confirmed"] = True
            current_app.db.users.update_one({"email": email}, {"$set": {"confirmed": requested_user["confirmed"]}})
            flash(message="Your email address has been confirmed. Thank you for registering!", category="success")

        else:
            flash(message="There was an error confirming your email address. Please try again.", category="danger")
    except SignatureExpired:
        flash(message="The confirmation link has expired. Please request a new confirmation email.", category="danger")
    except BadSignature:
        flash(message="The confirmation link is invalid. Please request a new confirmation email.", category="danger")
    except Exception as e:
        flash(message="An error occurred while confirming your email address. Please try again later.",
              category="danger")
        print(e)  # print the error message for debugging purposes
    return redirect(url_for('.login'))


@pages.route("/login", methods=["GET", "POST"])
def login():
    if session.get("email"):
        return redirect(url_for(".index"))

    form = LoginForm()
    if form.validate_on_submit():
        user_data = current_app.db.users.find_one({"email": form.email.data})

        if not user_data:
            flash(message=f"That email does not exist, please try again.")
            return redirect(url_for('.login'))

        # Email exists and password correct
        elif user_data["confirmed"]:
            current_user = User(**user_data)
            hashed_password = current_user.password
            unhashed_password = form.password.data
            if check_password_hash(pwhash=hashed_password, password=unhashed_password):
                session["user_id"] = current_user.id
                session["email"] = current_user.email
                session["name"] = current_user.name
                # flash(message=f"You have been Successfully Logged in!", category="success")
                return redirect(url_for(".index"))

            # Password incorrect
            else:
                flash(message=f"You have entered a wrong password! Please try again!", category="danger")
                return redirect(url_for('.login'))

        # Check if the mail is not confirmed
        else:
            flash(message=f"Please confirm your email to log in!", category="danger")

    return render_template("login.html", form=form, title="Movies Watchlist - Login")


@pages.route("/logout")
def logout():
    # session.clear() : don't want reset dark mode to light ! want to keep session["theme"]
    del session["user_id"]
    del session["email"]
    del session["name"]
    return redirect(url_for(".login"))


@pages.route("/")
@login_required
def index():
    user_data = current_app.db.users.find_one({"email": session["email"]})
    current_user = User(**user_data)
    # display movies where their id is "in" user.movies list of ids
    all_movies = current_app.db.movie.find({"_id": {"$in": current_user.movies}})
    # print(all_movies)
    movies_list = [Movie(**movie_data) for movie_data in all_movies]
    # print("movies list", movies_list)
    return render_template("index.html", title="Movies Watchlist", movies_data=movies_list)


@pages.route('/add', methods=['GET', 'POST'])
@login_required
def add_movie():
    form = MovieForm()
    if form.validate_on_submit():
        flash("Movie added successfully.")

        new_movie = Movie(
            _id=uuid.uuid4().hex,
            title=form.title.data,
            director=form.director.data,
            year=form.year.data
        )
        # inject new movie to db
        current_app.db.movie.insert_one(asdict(new_movie))
        # add movie._id to the current user movies list
        current_app.db.users.update_one({"_id": session["user_id"]}, {"$push": {"movies": new_movie.id}})

        return redirect(url_for(".index"))

    return render_template("new_movie.html", form=form, title="Movies Watchlist - Add a Movie")


@pages.get("/movie/<string:_id>")
@login_required
def movie(_id: str):
    movie_data = current_app.db.movie.find_one({"_id": _id})
    # print("movie", movie_data)
    if not movie_data:
        abort(404)
    current_movie = Movie(**movie_data)
    # print("current_movie", current_movie)
    return render_template("movie_details.html", movie=current_movie, title="Movies Watchlist - Movie details")


@pages.route("/edit/<string:_id>", methods=["GET", "POST"])
@login_required
def edit_movie(_id: str):
    movie_to_edit = Movie(**current_app.db.movie.find_one({"_id": _id}))
    # render the fields with the existing data already from db
    form = ExtendedMovieForm(obj=movie_to_edit)
    # updating movie fields
    if form.validate_on_submit():
        movie_to_edit.cast = form.cast.data
        movie_to_edit.tags = form.tags.data
        movie_to_edit.series = form.series.data
        movie_to_edit.description = form.description.data
        movie_to_edit.video_link = form.video_link.data

        current_app.db.movie.update_one({"_id": _id},
                                        {"$set": asdict(movie_to_edit)})

        return redirect(url_for(".movie", _id=_id))

    return render_template("movie_form.html", form=form, movie=movie_to_edit)


@pages.get("/movie/<string:_id>/rate")
@login_required
def rate_movie(_id: str):
    rating = int(request.args.get("rating"))  # You must add rating value in jinja like _id
    current_app.db.movie.update_one({"_id": _id}, {"$set": {"rating": rating}})
    return redirect(url_for(".movie", _id=_id))


@pages.get("/movie/<string:_id>/watch")
@login_required
def watch_today(_id: str):
    current_app.db.movie.update_one({"_id": _id}, {"$set": {"last_watched": current_day}})
    return redirect(url_for(".movie", _id=_id))


# @pages.route('/validate', methods=['POST'])
# def validate_add_movie():
# """Async with jquery ajax"""

#     form = MovieForm(request.form)
#     if form.validate_on_submit():
#         # Add the movie to the database or do some other processing here
#         return jsonify({'success': 'Movie added successfully.'})
#     else:
#         # Return error messages as JSON
#         error_messages = ', '.join([str(error) for error in form.errors.values()])
#         return jsonify({'error': error_messages})


@pages.get("/toggle-theme")
def toggle_theme():
    current_theme = session.get("theme")
    if current_theme == "dark":
        session["theme"] = "light"

    else:
        session["theme"] = "dark"

    return redirect(request.args.get("current_page"))
