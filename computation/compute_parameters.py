from computation.parameter_config import ParameterConfigs, ParameterType
from computation.landmark_parser import LandmarkParser
from scipy.spatial.transform import Rotation
from threading import Lock
from copy import deepcopy


class ParameterComputerResults:
    def __init__(self, outputs, landmarks, blendshapes, timestamp):
        self.outputs = outputs
        self.landmarks = landmarks
        self.blendshapes = blendshapes
        self.timestamp = timestamp

    @property
    def output_dict(self):
        return {output["id"]: output["value"] for output in self.outputs}


class ParameterComputer:
    def __init__(self, save_results: bool = False):
        self.parameter_configs = ParameterConfigs()
        self.save_results = save_results
        self.results = None
        self.lock = Lock()

    def get_parameter(self, id, value):
        return [{"id": id, "value": value}]

    def compute_translation_rotation(self, transformation_matrix):
        output = []

        pos_of = self.parameter_configs.face_position_offset
        rot_of = self.parameter_configs.face_rotation_offset

        translation_vector = transformation_matrix[:3, 3]
        output += self.get_parameter(
            "FacePositionX", (-translation_vector[0]) - pos_of[0]
        )
        output += self.get_parameter(
            "FacePositionY", (translation_vector[1]) - pos_of[1]
        )
        output += self.get_parameter(
            "FacePositionZ", (-translation_vector[2]) - pos_of[2]
        )

        rotation_matrix = transformation_matrix[:3, :3]
        r = Rotation.from_matrix(rotation_matrix)
        angles = r.as_euler("zyx", degrees=True)
        output += self.get_parameter("FaceAngleX", (-angles[1]) - rot_of[0])
        output += self.get_parameter("FaceAngleY", (-angles[2]) - rot_of[1])
        output += self.get_parameter("FaceAngleZ", angles[0] - rot_of[2])
        return output

    def create_blendshapes_dict(self, blendshape_list):
        shapes = {}
        for shape in blendshape_list:
            shapes[shape.category_name] = shape.score
        return shapes

    def compute_parameters(self, detection_result, timestamp):
        face_blendshapes_list = detection_result.face_blendshapes
        if len(face_blendshapes_list) == 0:
            # Do nothing if no shapes found
            return []

        face_blendshapes = self.create_blendshapes_dict(face_blendshapes_list[0])

        face_landmarks = detection_result.face_landmarks[0]
        landmark_parser = LandmarkParser(face_landmarks)
        landmark_sets = landmark_parser.get_landmark_sets()

        transformation_matrix = detection_result.facial_transformation_matrixes[0]

        # Compute Parameters from results
        output = []
        for parameter in self.parameter_configs.parameters:
            match parameter.parameter_type:
                case ParameterType.BLENDSHAPE:
                    output += parameter.parameter.compute_value(face_blendshapes)
                case ParameterType.LANDMARK:
                    output += parameter.parameter.compute_value(landmark_sets)

        output += self.compute_translation_rotation(transformation_matrix)

        if self.save_results:
            with self.lock:
                self.results = ParameterComputerResults(
                    output, landmark_sets, face_blendshapes, timestamp
                )

        return output

    def get_results(self):
        if self.results != None:
            with self.lock:
                return deepcopy(self.results)
        else:
            return None
