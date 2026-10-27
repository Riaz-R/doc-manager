from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def home():
        return "<h1>Doc Manager</h1><p>The app is running.</p>"

    return app
