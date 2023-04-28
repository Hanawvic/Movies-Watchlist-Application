from flask import Flask
from pymongo import MongoClient
from flask_mail import Mail
from movie_library.config import Config


mail = Mail()
client = MongoClient(Config.MONGODB_URI)
db = client.movies


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    mail.init_app(app)
    # app.db = MongoClient(app.config["MONGODB_URI"]).get_default_database()
    with app.app_context():
        app.db = db
        from movie_library.routes import pages
        app.register_blueprint(pages)

    return app
