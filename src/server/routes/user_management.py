from time import strftime
from flask import Blueprint, current_app, jsonify, request
from flask_praetorian import auth_required, roles_accepted

# Core and Flask, and functionality
from server import redis_store, ACCESS_EXPIRES
from server.extensions import db, guard, redis_store
from server.utils import log_redis

# Models
from server.models.users import User

user_manager_blueprint = Blueprint("user-management", __name__)

@user_manager_blueprint.route("/api/v2/login", methods=["POST"])
def do_login():
    identifier = request.json.get("identifier", None)
    password = request.json.get("password", None)
    if identifier is None or password is None:
        return (
            jsonify(error=401, message=f"Missing user: {identifier} or password: {password}"),
            401,
        )

    log_redis(current_app.config.get("REDIS_ROOT_LOGGER"), f"Received login request from {request.remote_addr} for: {identifier}")
    user = User.query.filter_by(username=identifier).first()
    email = User.query.filter_by(email=identifier).first()
    identifier = email if user is None else user
    if identifier is None:
        return (jsonify(error=401, message=f"User not found"), 401)

    t_now = strftime("%d/%m/%Y %H:%M")
    identifier.last_login = t_now
    log_redis(identifier.username, f"User logged in at {t_now}")
    db.session.commit()
    user = guard.authenticate(identifier.username, password)
    token = guard.encode_jwt_token(user)
    # We can either set the token in the response cookie, or send it to client to store in the localstorage,
    # Reference: https://developer.mozilla.org/en-US/docs/Web/API/document/cookie
    # resp = make_response({"message": f"Logged in as {identifier}", "access_token": token})
    # resp.set_cookie("access_token", value=token)
    return (
        jsonify(
            {"message": f"Logged in as {identifier.username}", "access_token": token}
        ),
        200,
    )


@user_manager_blueprint.route("/api/v2/register", methods=["POST"])
@roles_accepted("admin")
def register_user():
    content = request.json
    username = content.get("username", None)
    email = content.get("email", None)
    password = content.get("password", None)
    log_redis(current_app.config.get("REDIS_ROOT_LOGGER"), f"Received register request from {request.remote_addr} for: {username}->{email}")

    if (username is None and email is None) or password is None:
        return (
            jsonify(error=400, message=f"Missing user: {username} or password: {password}"),
            400,
        )

    user_exists = User.query.filter_by(username=username).first() is not None
    email_exists = User.query.filter_by(email=email).first() is not None


    if user_exists or email_exists:
        return (jsonify(error=400, message="Invalid data, check your input"), 400)

    hashed_password = guard.hash_password(password)
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return (jsonify(
        {"id": new_user.id, "username": new_user.username, "email": new_user.email}
    ), 200)


@user_manager_blueprint.route("/api/v2/account-status", methods=["GET"])
@auth_required
def check_account_status():   
    identifier = request.json.get("identifier", None)
    log_redis(current_app.config.get("REDIS_ROOT_LOGGER"), f"Received status request from {request.remote_addr} for: {identifier}")
    if identifier is None:
        return (
            jsonify(error=400, message="Please provide a valid identifier (Username|Email)"),
            400,
        )

    user = User.query.filter_by(username=identifier).first()
    email = User.query.filter_by(email=identifier).first()
    identifier = email if user is None else user
    if identifier is None:
        return (jsonify(error=404, message=f"The user {identifier} does not seem to exist"), 404)

    status = "Active" if identifier.is_active else "Deactivated"
    return jsonify(message=f"User {identifier.username} is {status}")


@user_manager_blueprint.route("/api/v2/change-account-status", methods=["POST"])
@roles_accepted("admin")
def deactivate_account():
    identifier = request.json.get("identifier", None)
    log_redis(current_app.config.get("REDIS_ROOT_LOGGER"), f"Received change status request from {request.remote_addr} for: {identifier}")
    if identifier is None:
        return (
            jsonify(error=400, message="Please provide a valid identifier (Username|Email)"),
            400,
        )

    user = User.query.filter_by(username=identifier).first()
    email = User.query.filter_by(email=identifier).first()
    identifier = email if user is None else user
    if identifier is None:
        return (jsonify(error=404, message=f"The user {identifier} does not seem to exist"), 404)

    identifier.is_active = not identifier.is_active
    db.session.commit()
    return jsonify(
        message=f"User {identifier.username} Status = ({identifier.is_active})"
    )


@user_manager_blueprint.route("/api/v2/refresh-token", methods=["POST"])
def refresh_token():
    old_token = guard.read_token_from_header()
    id = guard.extract_jwt_token(old_token).get("id")
    log_redis(current_app.config.get("REDIS_ROOT_LOGGER"), f"Received refresh token request from {request.remote_addr} for user with ID: {id}")
    new_token = guard.refresh_jwt_token(old_token)
    ret = {"access_token": new_token}
    return jsonify(ret), 200


@user_manager_blueprint.route("/api/v2/check-token", methods=["GET"])
@auth_required
def check_if_token_is_revoked():
    token = guard.read_token_from_header()
    data = guard.extract_jwt_token(token)
    id = data.get("id")
    log_redis(current_app.config.get("REDIS_ROOT_LOGGER"), f"Received check token request from {request.remote_addr} for user with ID: {id}")
    current_app.logger.debug(f"DATA: {data}")
    token_in_redis = redis_store.get(data["jti"])
    current_app.logger.debug(f"TOKEN: {token_in_redis}")
    if token_in_redis is None:
        return jsonify(message=f"token allowed ({token})")
    return jsonify(message=f"token blacklisted ({token})")


@user_manager_blueprint.route("/api/v2/blacklist-token", methods=["GET"])
@auth_required
def do_logout():
    token = guard.read_token_from_header()
    data = guard.extract_jwt_token(token)
    id = data.get("id")
    log_redis(current_app.config.get("REDIS_ROOT_LOGGER"), f"Received blacklist token request from {request.remote_addr} for user with ID: {id}")
    redis_store.set(data["jti"], "", ex=ACCESS_EXPIRES)
    return jsonify(message="token blacklisted ({})".format(token))
