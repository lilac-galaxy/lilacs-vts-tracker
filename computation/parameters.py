from enum import Enum
import numpy as np
from skimage.measure import EllipseModel
from scipy.spatial import ConvexHull


class BaseParameter:
    # min and max only used if clamp is true
    def __init__(
        self,
        name: str,
        output_id: str,
        scale: float = 1.0,
        offset: float = 0.0,
        clamp: bool = True,
        min_val: float = 0.0,
        max_val: float = 1.0,
    ):
        self.name = name
        self.output_id = output_id
        self.scale = scale
        self.offset = offset
        self.clamp = clamp
        self.min_val = min_val
        self.max_val = max_val
        assert (
            self.min_val <= self.max_val
        ), "Min value for parameter must be less than max value"

    def set_clamp(self, state):
        self.clamp = state

    def compute_value(self):
        value = (self.value - self.offset) * self.scale
        if self.clamp:
            value = max(min(value, self.max_val), self.min_val)
        return [{"id": self.output_id, "value": value}]

    def serialize(self):
        param_dict = {
            "name": self.name,
            "output_id": self.output_id,
            "scale": self.scale,
            "offset": self.offset,
            "clamp": self.clamp,
            "min_val": self.min_val,
            "max_val": self.max_val,
        }
        return param_dict


class InputBlendshapeOption:
    def __init__(
        self,
        name,
        sign: int = 1,
    ):
        self.name = name
        self.sign = sign

    def __eq__(self, value):
        return value == self.name

    def serialize(self):
        return {"name": self.name, "sign": self.sign}


class BlendshapeParameter(BaseParameter):
    def __init__(
        self,
        name: str,
        input_parameters: list[InputBlendshapeOption],
        output_id: str,
        scale: float = 1.0,
        offset: float = 0.0,
        clamp: bool = True,
        min_val: float = 0.0,
        max_val: float = 1.0,
    ):
        super().__init__(name, output_id, scale, offset, clamp, min_val, max_val)
        self.input_parameters = []
        for parameter in input_parameters:
            if type(parameter) == dict:
                self.input_parameters.append(InputBlendshapeOption(**parameter))
            else:
                self.input_parameters.append(parameter)

    def compute_value(self, blendshapes: dict):
        self.value = 0
        pos_value = 0
        neg_value = 0
        for parameter in self.input_parameters:
            if parameter.sign == 1:
                pos_value = max(pos_value, blendshapes[parameter.name])
            elif parameter.sign == -1:
                neg_value = max(neg_value, blendshapes[parameter.name])
        self.value = pos_value - neg_value
        return super().compute_value()

    def serialize(self):
        param_dict = super().serialize()

        input_param = []
        for param in self.input_parameters:
            input_param.append(param.serialize())
        param_dict |= {"input_parameters": input_param}
        return param_dict


class LandmarkCalculateOption(Enum):
    ELLIPSE_FIT = 1
    HULL_CALCUATION = 2


class LandmarkParameter(BaseParameter):
    def __init__(
        self,
        name: str,
        input_landmark_set: str,
        calculate_option: LandmarkCalculateOption,
        output_id: str,
        scale: float = 1,
        offset: float = 0,
        clamp: bool = True,
        min_val: float = 0.0,
        max_val: float = 1.0,
    ):
        super().__init__(name, output_id, scale, offset, clamp, min_val, max_val)
        self.input_landmark_set = input_landmark_set
        if type(calculate_option) == str:
            self.calculate_option = LandmarkCalculateOption[calculate_option]
        elif type(calculate_option) == int:
            self.calculate_option = LandmarkCalculateOption(calculate_option)
        else:
            self.calculate_option = calculate_option

    def calculate_ellipse_minor_major_ratio(self, landmark_points):
        ellipse_array = np.array(landmark_points)
        ell = EllipseModel()
        ell.estimate(ellipse_array)
        _, _, a, b, _ = ell.params
        return b / a

    def get_hull(self, points):
        point_array = np.array(points)
        return ConvexHull(points=point_array)

    def calculate_hull(self, landmark_points, oval_points):
        face_hull = self.get_hull(oval_points)
        landmark_hull = self.get_hull(landmark_points)
        landmark_share = 0
        if face_hull != None and landmark_hull != None:
            landmark_share = landmark_hull.area / face_hull.area
        return landmark_share

    def compute_value(self, landmark_sets: dict):
        landmark_points = landmark_sets[self.input_landmark_set]
        match self.calculate_option:
            case LandmarkCalculateOption.ELLIPSE_FIT:
                self.value = self.calculate_ellipse_minor_major_ratio(landmark_points)
            case LandmarkCalculateOption.HULL_CALCUATION:
                oval_points = landmark_sets["face_oval_xyz"]
                self.value = self.calculate_hull(landmark_points, oval_points)
        return super().compute_value()

    def serialize(self):
        param_dict = super().serialize()
        param_dict |= {
            "input_landmark_set": self.input_landmark_set,
            "calculate_option": self.calculate_option.name,
        }
        return param_dict


class ParameterType(Enum):
    BLENDSHAPE = 1
    LANDMARK = 2


class Parameter:
    def __init__(self, parameter_type, *args, **kwargs):
        if type(parameter_type) == str:
            self.parameter_type = ParameterType[parameter_type]
        elif type(parameter_type) == int:
            self.parameter_type = ParameterType(parameter_type)
        else:
            self.parameter_type = parameter_type
        match self.parameter_type:
            case ParameterType.BLENDSHAPE:
                self.parameter = BlendshapeParameter(*args, **kwargs)
            case ParameterType.LANDMARK:
                self.parameter = LandmarkParameter(*args, **kwargs)

    def serialize(self):
        param_dict = {"parameter_type": self.parameter_type.name}
        param_dict |= self.parameter.serialize()
        return param_dict

    def __str__(self):
        data = self.serialize()
        return str(data)
