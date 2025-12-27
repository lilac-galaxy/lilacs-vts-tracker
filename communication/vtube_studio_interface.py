import json
import os
from websockets.sync.client import connect


class VTSInterface:
    def __init__(self, address: str, auth_file: str):
        self.websocket = connect(address)
        if auth_file == "":
            raise Exception("Authentication filepath cannot be empty!")
        self.auth_file = auth_file
        self.auth_token = ""

        if os.path.isfile(self.auth_file):
            with open(self.auth_file, "r") as fp:
                auth_file_data = json.load(fp)
                self.auth_token = auth_file_data["auth_token"]

        if self.auth_token == "":
            # First time setup
            self.get_authentication_token()

        self.authenticate()

    def close(self):
        if self.websocket:
            self.websocket.close()

    def __del__(self):
        if self.websocket:
            self.websocket.close()

    # Request authentication
    def get_authentication_token(self):
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "lilacs-vts-face-tracker",
            "messageType": "AuthenticationTokenRequest",
            "data": {
                "pluginName": "Lilac's VTS Face Tracker",
                "pluginDeveloper": "lilacGalaxy",
            },
        }
        request_json = json.dumps(request)
        self.websocket.send(request_json)
        response_json = self.websocket.recv()
        response = json.loads(response_json)
        response_message_type = response["messageType"]
        if response_message_type == "AuthenticationTokenResponse":
            self.auth_token = response["data"]["authenticationToken"]
            with open(self.auth_file, "w") as auth_json:
                auth_token_data = {
                    "auth_token": response["data"]["authenticationToken"]
                }
                auth_json.write(json.dumps(auth_token_data, indent=4))
        else:
            raise Exception(
                f"Received message type '{response_message_type}' when \
                    expecting 'AuthenticationTokenResponse'. No Token Created"
            )

    def authenticate(self):
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "lilacs-vts-face-tracker",
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": "Lilac's VTS Face Tracker",
                "pluginDeveloper": "lilacGalaxy",
                "authenticationToken": self.auth_token,
            },
        }
        request_json = json.dumps(request)

        self.websocket.send(request_json)
        response_json = self.websocket.recv()
        response = json.loads(response_json)
        response_message_type = response["messageType"]
        if response_message_type == "AuthenticationResponse":
            print("Authentication Successful!")
        else:
            raise Exception(
                f"Received message type '{response_message_type}' when \
                    expecting 'AuthenticationResponse'. Cannot authenticate"
            )

    def parameter_creation_request(
        self, parameter_name, explanation, min_val=0, max_val=1, default_val=0
    ):
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "lilacs-vts-face-tracker",
            "messageType": "ParameterCreationRequest",
            "data": {
                "parameterName": parameter_name,
                "explanation": explanation,
                "min": min_val,
                "max": max_val,
                "defaultValue": default_val,
            },
        }
        return json.dumps(request)

    def create_parameter(
        self, websocket, name, description, min_val, max_val, default_val
    ):
        request_message_json = self.parameter_creation_request(
            name, description, min_val, max_val, default_val
        )
        websocket.send(request_message_json)
        _ = websocket.recv()

    def send_detection_parameter_results(self, detection_param_values):
        face_found = len(detection_param_values) > 0
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "lilacs-vts-face-tracker",
            "messageType": "InjectParameterDataRequest",
            "data": {
                "faceFound": face_found,
                "mode": "add",
                "parameterValues": detection_param_values,
            },
        }

        # only write if there are parameters to set
        if len(request["data"]["parameterValues"]) > 0:
            request_json = json.dumps(request)
            self.websocket.send(request_json)
            _ = self.websocket.recv(decode=False)
