from flask import render_template, Blueprint, url_for


main_blueprint = Blueprint(
    "main", __name__, static_folder="../../build", template_folder="../../build"
)


@main_blueprint.route("/")
def react():
    return render_template("index.html")


@main_blueprint.route("/<path:path>", methods=["GET", "POST"])
def catch_all(path):
    if "favicon" in path:
        return url_for("main.static", filename="favicon.ico")
    elif "manifest" in path:
        return url_for("main.static", filename="manifest.json")
    else:
        return render_template("index.html")
