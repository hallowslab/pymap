from flask.cli import FlaskGroup

from server import create_flask_app


app = create_flask_app()
cli = FlaskGroup(create_app=create_flask_app)


if __name__ == "__main__":
    cli()
