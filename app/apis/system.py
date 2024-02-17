import requests
from flask import current_app as ca
from flask_restx import Namespace, Resource, abort

from .models import (
    message,
)

api = Namespace(
    "system",
    description="System API",
    # decorators=[token_required, role_required("max")],
)

api.add_model("Error", message)


@api.response(422, "Error", message)
@api.route("/version")
# @auth_required()
class Version(Resource):
    def get(self):
        try:
            response = requests.get(ca.config["GIT_URL"], timeout=ca.config["TIMEOUT"])
            response.raise_for_status()
            rjson = response.json()
            rjson["app_version"] = rjson.get("tag_name").replace("v", "")
            current_version = ca.config["VERSION"].replace("v", "")
            rjson.update(
                {
                    "current_version": current_version,
                    # "update_available": semver.compare(
                    #     rjson["app_version"], current_version
                    # ),
                }
            )
            return rjson
        except requests.RequestException as error:
            abort(422, str(error))
