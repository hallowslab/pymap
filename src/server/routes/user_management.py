from flask import Blueprint, jsonify, request, url_for, current_app, abort, redirect
from flask_praetorian import auth_required, roles_accepted

# Core and Flask
from server import db, guard, jwt_redis_blocklist, ACCESS_EXPIRES
from server.tasks import call_system

# Models
from server.models.users import User

user_manager_blueprint = Blueprint("apiV2", __name__)


@user_manager_blueprint.route("/api/v2/login", methods=["POST"])
def do_login():
    identifier = request.json.get("identifier", None)
    password = request.json.get("password", None)
    if identifier is None or password is None:
        abort(401)

    user = User.query.filter_by(username=identifier).first()
    email = User.query.filter_by(email=identifier).first()
    identifier = email if user is None else user
    if identifier:
        user = guard.authenticate(identifier.username, password)
        ret = {"access_token": guard.encode_jwt_token(user)}
        return (jsonify(ret), 200)
    abort(401)


@user_manager_blueprint.route("/api/v2/logout", methods=["GET"])
@auth_required
def do_logout():
    token = guard.read_token_from_header()
    data = guard.extract_jwt_token(token)
    jwt_redis_blocklist.set(data["jti"], "", ex=ACCESS_EXPIRES)
    return jsonify(message="token blacklisted ({})".format(token))


@user_manager_blueprint.route("/api/v2/register", methods=["POST"])
@roles_accepted("admin")
def register_user():
    content = request.json
    username = content.get("username", None)
    email = content.get("email", None)
    password = content.get("password", None)

    user_exists = User.query.filter_by(username=username).first() is not None
    email_exists = User.query.filter_by(email=email).first() is not None

    if user_exists or email_exists or password is None:
        abort(409)

    hashed_password = guard.hash_password(password)
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify(
        {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
        }
    )


@user_manager_blueprint.route("/api/v2/account-status", methods=["GET"])
def check_if_token_is_revoked():
    token = guard.read_token_from_header()
    data = guard.extract_jwt_token(token)
    current_app.logger.debug(f"DATA: {data}")
    token_in_redis = jwt_redis_blocklist.get(data["jti"])
    current_app.logger.debug(f"TOKEN: {token_in_redis}")
    if token_in_redis is None:
        return jsonify(f"token allowed ({token})")
    return jsonify(f"token blacklisted ({token})")


@user_manager_blueprint.route("/api/v2/change-account-status", methods=["POST"])
@roles_accepted("admin")
def deactivate_account():
    identifier = request.json.get("identifier", None)
    if identifier is None:
        abort(400)

    user = User.query.filter_by(username=identifier).first()
    email = User.query.filter_by(email=identifier).first()
    identifier = email if user is None else user
    if identifier:
        identifier.is_active = not identifier.is_active
        return jsonify(message="User deactivated ({})".format(identifier.username))
    abort(404)
