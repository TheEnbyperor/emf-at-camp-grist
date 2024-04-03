import os

import flask
import dotenv


def create_app() -> flask.Flask:
    dotenv.load_dotenv()

    app = flask.Flask(__name__)
    app.config.from_mapping(
        GRIST_DOCUMENT_ID=os.getenv("GRIST_DOCUMENT_ID"),
        GRIST_TABLE_ID=os.getenv("GRIST_TABLE_ID"),
        GRIST_API_KEY=os.getenv("GRIST_API_KEY"),
        GRIST_BASE_URL=os.getenv("GRIST_BASE_URL"),
        ZONE_FILE_LOCATION=os.getenv("ZONE_FILE_LOCATION"),
        KNOT_SOCKET_LOCATION=os.getenv("KNOT_SOCKET_LOCATION"),
    )
    app.config.from_prefixed_env()
    return app
