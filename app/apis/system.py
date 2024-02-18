import requests
from flask import current_app as ca
from flask_restx import Namespace, Resource, abort
from flask_security import auth_required, roles_required

from .models import message

api = Namespace("system", description="System API")

api.add_model("Error", message)


@api.response(422, "Error", message)
@api.route("/version")
class Version(Resource):
    @auth_required()
    @roles_required("admin")
    def get(self):
        try:
            response = requests.get(ca.config["GIT_URL"], timeout=3)
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
