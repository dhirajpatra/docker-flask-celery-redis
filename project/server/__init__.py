# project/server/__init__.py


import os

from flask import Flask
from flask_bootstrap import Bootstrap
# from flask_pymongo import PyMongo
# from pymongo import MongoClient, errors


# instantiate the extensions
bootstrap = Bootstrap()


def create_app(script_info=None):

    # instantiate the app
    app = Flask(
        __name__,
        template_folder="../client/templates",
        static_folder="../client/static",
    )

    # set config
    app_settings = os.getenv("APP_SETTINGS")
    app.config.from_object(app_settings)

    # set up extensions
    bootstrap.init_app(app)

    # register blueprints
    from server.main.views import main_blueprint

    app.register_blueprint(main_blueprint)

    # shell context for flask cli
    app.shell_context_processor({"app": app})

    # db 
    # app.db = connect_mongo_db(app)

    return app


# def connect_mongo_db(app):
#     app.config['MONGO_URI'] = 'mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/' + os.environ['MONGODB_DATABASE']
#     # app.config['MONGO_URI'] = 'mongodb://' + os.environ['MONGODB_HOSTNAME'] + ':27017/'
#     db = None
    
#     try:
#         # start database
#         mongo = MongoClient(app.config["MONGO_URI"], connect=False)
#         # mongo = PyMongo(app)
#         db = mongo.log_upload_s3
#         # db.logs.insert_one({
#         #     "mac": "ff4v-fdf4-j7j8-3f44",
#         #     "file_name": "actual.log",
#         #     "start_time": "324224443434347",
#         #     "end_time": "535346345344"
#         # })

#     except errors.ServerSelectionTimeoutError as err:
#         # set the client and DB name list to 'None' and `[]` if exception
#         mongo = None

#         # catch pymongo.errors.ServerSelectionTimeoutError
#         print ("pymongo ERROR:", err)

#     return db