from flask import Blueprint
from ..controllers.medical_assistant_controller import medical_assistant_controller

api_routes = Blueprint('api', __name__)
api_routes.register_blueprint(medical_assistant_controller)
