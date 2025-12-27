from computation.parameters import (
    LandmarkCalculateOption,
    InputBlendshapeOption,
    ParameterType,
    Parameter,
)
import os
import json


class ParameterConfigs:
    def __init__(self, params_file="parameters.json"):
        self.parameters = []
        self.face_position_offset: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.face_rotation_offset: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.params_file = params_file
        self.init()

    def file_save(self):
        with open(self.params_file, "w") as fp:
            parameters_out = []
            for parameter in self.parameters:
                parameters_out.append(parameter.serialize())
            fp.write(
                json.dumps(
                    {
                        "parameters": parameters_out,
                        "face_position_offset": self.face_position_offset,
                        "face_rotation_offset": self.face_rotation_offset,
                    },
                    indent=4,
                )
            )

    def config_reset(self):
        self.parameters.clear()
        self.init()

    def config_defaults(self):
        self.parameters.clear()
        self.default_init()

    def init(self):
        if os.path.isfile(self.params_file):
            self.file_init()
        else:
            self.default_init()

    def file_init(self):
        with open(self.params_file, "r") as fp:
            params_data = json.load(fp)
            for parameter in params_data["parameters"]:
                new_param = Parameter(**parameter)
                self.parameters.append(new_param)
            if "face_position_offset" in params_data:
                self.face_position_offset = tuple(
                    params_data["face_position_offset"]
                )
            if "face_rotation_offset" in params_data:
                self.face_rotation_offset = tuple(
                    params_data["face_rotation_offset"]
                )

    def default_init(self):
        self.parameters.append(
            Parameter(
                ParameterType.BLENDSHAPE,
                "Brows Shape",
                [
                    InputBlendshapeOption("browInnerUp", 1),
                    InputBlendshapeOption("browOuterUpLeft", 1),
                    InputBlendshapeOption("browOuterUpRight", 1),
                    InputBlendshapeOption("browDownLeft", -1),
                    InputBlendshapeOption("browDownRight", -1),
                ],
                "Brows",
                clamp=False,
            )
        )

        self.parameters.append(
            Parameter(
                ParameterType.BLENDSHAPE,
                "Brow Left Y",
                [
                    InputBlendshapeOption("browInnerUp", 1),
                    InputBlendshapeOption("browOuterUpLeft", 1),
                    InputBlendshapeOption("browDownLeft", -1),
                ],
                "BrowLeftY",
                clamp=False,
            )
        )

        self.parameters.append(
            Parameter(
                ParameterType.BLENDSHAPE,
                "Brow Right Y",
                [
                    InputBlendshapeOption("browInnerUp", 1),
                    InputBlendshapeOption("browOuterUpRight", 1),
                    InputBlendshapeOption("browDownRight", -1),
                ],
                "BrowRightY",
                clamp=False,
            )
        )

        self.parameters.append(
            Parameter(
                ParameterType.LANDMARK,
                "Cheek Puff",
                "face_oval_xy",
                LandmarkCalculateOption.ELLIPSE_FIT,
                "CheekPuff",
                scale=20,
                offset=0.65,
            )
        )

        self.parameters.append(
            Parameter(
                ParameterType.LANDMARK,
                "Left Eye Open",
                "left_eye_xy",
                LandmarkCalculateOption.ELLIPSE_FIT,
                "EyeOpenLeft",
                10,
                0.3,
            )
        )
        self.parameters.append(
            Parameter(
                ParameterType.LANDMARK,
                "Right Eye Open",
                "right_eye_xy",
                LandmarkCalculateOption.ELLIPSE_FIT,
                "EyeOpenRight",
                10,
                0.3,
            )
        )

        self.parameters.append(
            Parameter(
                ParameterType.BLENDSHAPE,
                "Left Eye X",
                [
                    InputBlendshapeOption("eyeLookOutLeft", 1),
                    InputBlendshapeOption("eyeLookInLeft", -1),
                ],
                "EyeLeftX",
                clamp=False,
            )
        )

        self.parameters.append(
            Parameter(
                ParameterType.BLENDSHAPE,
                "Right Eye X",
                [
                    InputBlendshapeOption("eyeLookOutRight", -1),
                    InputBlendshapeOption("eyeLookInRight", 1),
                ],
                "EyeRightX",
                clamp=False,
            )
        )

        self.parameters.append(
            Parameter(
                ParameterType.BLENDSHAPE,
                "Left Eye Y",
                [
                    InputBlendshapeOption("eyeLookUpLeft", 1),
                    InputBlendshapeOption("eyeLookDownLeft", -1),
                ],
                "EyeLeftY",
                clamp=False,
            )
        )

        self.parameters.append(
            Parameter(
                ParameterType.BLENDSHAPE,
                "Right Eye Y",
                [
                    InputBlendshapeOption("eyeLookUpRight", 1),
                    InputBlendshapeOption("eyeLookDownRight", -1),
                ],
                "EyeRightY",
                clamp=False,
            )
        )

        self.parameters.append(
            Parameter(
                ParameterType.LANDMARK,
                "Mouth Open",
                "lips_xyz",
                LandmarkCalculateOption.HULL_CALCULATION,
                "MouthOpen",
                clamp=False,
                scale=20,
                offset=0.035,
            )
        )

        self.parameters.append(
            Parameter(
                ParameterType.LANDMARK,
                "Mouth Open Plus Volume",
                "lips_xyz",
                LandmarkCalculateOption.HULL_CALCULATION,
                "VoiceVolumePlusMouthOpen",
                clamp=False,
                scale=20,
                offset=0.045,
            )
        )

        self.parameters.append(
            Parameter(
                ParameterType.BLENDSHAPE,
                "Mouth Smile",
                [
                    InputBlendshapeOption("mouthSmileLeft", 1),
                    InputBlendshapeOption("mouthSmileRight", 1),
                    InputBlendshapeOption("mouthPucker", -1),
                    InputBlendshapeOption("mouthShrugLower", -1),
                ],
                "MouthSmile",
                clamp=False,
            )
        )

        self.parameters.append(
            Parameter(
                ParameterType.BLENDSHAPE,
                "Mouth Smile Plus Frequency",
                [
                    InputBlendshapeOption("mouthSmileLeft", 1),
                    InputBlendshapeOption("mouthSmileRight", 1),
                    InputBlendshapeOption("mouthPucker", -1),
                    InputBlendshapeOption("mouthShrugLower", -1),
                ],
                "VoiceFrequencyPlusMouthSmile",
                clamp=False,
                scale=0.5,
            )
        )

        self.parameters.append(
            Parameter(
                ParameterType.BLENDSHAPE,
                "Mouth X Blendshape",
                [
                    InputBlendshapeOption("mouthRight", 1),
                    InputBlendshapeOption("mouthPressRight", 1),
                    InputBlendshapeOption("mouthLeft", -1),
                    InputBlendshapeOption("mouthPressLeft", -1),
                ],
                "mouthX",
                scale=3.0,
                min_val=-1,
            )
        )
