from server import create_flask_app, db

db.create_all(app=create_flask_app())
