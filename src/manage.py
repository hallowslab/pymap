import click
from flask.cli import FlaskGroup

from server import create_flask_app, guard
from server.models import users, db
from flask.cli import with_appcontext


app = create_flask_app()
cli = FlaskGroup(create_app=create_flask_app)


@app.cli.command("create-user")
@click.argument("user")
def create_user(user):
    new_user = users.User(
        user, "pymap@localhost", guard.hash_password("CH4NG3_M$"), "admin"
    )
    db.session.add(new_user)
    db.session.commit()
    ctx_str = f"\nCreated User:\nUser: {user}\nEmail: {'pymap@localhost'}\nPassword: {'CH4NG3_M$'}\nRoles: {'admin'}======="
    print(ctx_str)


@app.cli.command("create-db")
@with_appcontext
def create_db():
    db.create_all()
    db.session.commit()


if __name__ == "__main__":
    cli()
