import ctypes
from imgui_bundle import imgui
import sdl2
import OpenGL.GL as gl

from imgui_bundle.python_backends.sdl2_backend import SDL2Renderer
from computation.parameter_config import ParameterConfigs
from computation.parameters import (
    BlendshapeParameter,
    LandmarkParameter,
    BaseParameter,
    LandmarkCalculateOption,
    ParameterType,
    Parameter,
)
from computation.compute_parameters import ParameterComputer


class Application:
    def __init__(self):
        imgui.create_context()
        self.window, self.gl_context = self.impl_pysdl2_init()
        self.impl = SDL2Renderer(self.window)
        self.event = sdl2.SDL_Event()
        self.should_close = False

    def __del__(self):
        if self.impl:
            self.impl.shutdown()
        if self.gl_context:
            sdl2.SDL_GL_DeleteContext(self.gl_context)
        if self.window:
            sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

    def impl_pysdl2_init(self):
        width, height = 1280, 720
        window_name = "Lilac's VTS Tracker"

        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) < 0:
            raise Exception(
                "Error: SDL could not initialize! SDL Error: "
                + sdl2.SDL_GetError().decode("utf-8")
            )

        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DOUBLEBUFFER, 1)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DEPTH_SIZE, 24)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_STENCIL_SIZE, 8)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_ACCELERATED_VISUAL, 1)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_MULTISAMPLEBUFFERS, 1)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_MULTISAMPLESAMPLES, 8)
        sdl2.SDL_GL_SetAttribute(
            sdl2.SDL_GL_CONTEXT_FLAGS,
            sdl2.SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG,
        )
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION, 4)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION, 1)
        sdl2.SDL_GL_SetAttribute(
            sdl2.SDL_GL_CONTEXT_PROFILE_MASK, sdl2.SDL_GL_CONTEXT_PROFILE_CORE
        )

        sdl2.SDL_SetHint(
            sdl2.SDL_HINT_MAC_CTRL_CLICK_EMULATE_RIGHT_CLICK, b"1"
        )
        sdl2.SDL_SetHint(sdl2.SDL_HINT_VIDEO_HIGHDPI_DISABLED, b"1")

        window = sdl2.SDL_CreateWindow(
            window_name.encode("utf-8"),
            sdl2.SDL_WINDOWPOS_CENTERED,
            sdl2.SDL_WINDOWPOS_CENTERED,
            width,
            height,
            sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_RESIZABLE,
        )

        if window is None:
            raise Exception(
                "Error: Window could not be created! SDL Error: "
                + sdl2.SDL_GetError().decode("utf-8")
            )

        gl_context = sdl2.SDL_GL_CreateContext(window)
        if gl_context is None:
            raise Exception(
                "Error: Cannot create OpenGL Context! SDL Error: "
                + sdl2.SDL_GetError().decode("utf-8")
            )

        sdl2.SDL_GL_MakeCurrent(window, gl_context)
        if sdl2.SDL_GL_SetSwapInterval(1) < 0:
            raise Exception(
                "Warning: Unable to set VSync! SDL Error: "
                + sdl2.SDL_GetError().decode("utf-8")
            )

        return window, gl_context

    def render_frame(self, computer: ParameterComputer):
        while sdl2.SDL_PollEvent(ctypes.byref(self.event)) != 0:
            if self.event.type == sdl2.SDL_QUIT:
                self.should_close = True
                return
            self.impl.process_event(self.event)
        self.impl.process_inputs()

        imgui.new_frame()
        self.draw_windows(computer)

        gl.glClearColor(0.1, 0.0, 0.2, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        self.impl.render(imgui.get_draw_data())
        sdl2.SDL_GL_SwapWindow(self.window)

    def draw_windows(self, computer: ParameterComputer):
        self.draw_parameter_window(computer.parameter_configs, computer)
        results = computer.get_results()
        blendshapes = None
        outputs = None
        landmarks = None
        if results is not None:
            blendshapes = results.blendshapes
            outputs = results.outputs
            landmarks = results.landmarks

        self.draw_blendshapes(blendshapes)
        self.draw_outputs(outputs)
        self.draw_landmarks(landmarks)

    def draw_landmark_set(self, x, y, offsets, draw_list, landmarks, color):
        for point in landmarks:
            center = imgui.ImVec2(
                x + ((offsets[0] - point[0])) * 1000,
                y + (point[1] - offsets[1]) * 1000,
            )
            draw_list.add_circle_filled(
                center,
                1,
                color,
            )

    def get_landmark_offset(self, landmarks):
        num_landmarks = len(landmarks["all_xy"])
        if num_landmarks <= 0:
            return (0.0, 0.0)
        sum_x = 0
        sum_y = 0
        for point in landmarks["all_xy"]:
            sum_x += point[0]
            sum_y += point[1]
        sum_x = sum_x / num_landmarks
        sum_y = sum_y / num_landmarks
        return (sum_x, sum_y)

    def draw_landmarks(self, landmarks):
        if imgui.begin("Landmarks Window")[0]:
            if landmarks is None:
                imgui.text("No Landmark Data Available")
            else:
                draw_list = imgui.get_window_draw_list()
                x, y = imgui.get_cursor_screen_pos()
                w_size_x, w_size_y = imgui.get_window_size()
                x += w_size_x // 2
                y += w_size_y // 2
                offsets = self.get_landmark_offset(landmarks)
                self.draw_landmark_set(
                    x,
                    y,
                    offsets,
                    draw_list,
                    landmarks["all_xy"],
                    imgui.get_color_u32(imgui.ImVec4(1, 1, 0, 1)),
                )
                self.draw_landmark_set(
                    x,
                    y,
                    offsets,
                    draw_list,
                    landmarks["lips_xy"],
                    imgui.get_color_u32(imgui.ImVec4(1, 0, 0, 1)),
                )
                self.draw_landmark_set(
                    x,
                    y,
                    offsets,
                    draw_list,
                    landmarks["left_eye_xy"],
                    imgui.get_color_u32(imgui.ImVec4(1, 0, 0, 1)),
                )
                self.draw_landmark_set(
                    x,
                    y,
                    offsets,
                    draw_list,
                    landmarks["right_eye_xy"],
                    imgui.get_color_u32(imgui.ImVec4(1, 0, 0, 1)),
                )
                self.draw_landmark_set(
                    x,
                    y,
                    offsets,
                    draw_list,
                    landmarks["left_eyebrow_xy"],
                    imgui.get_color_u32(imgui.ImVec4(1, 0, 0, 1)),
                )
                self.draw_landmark_set(
                    x,
                    y,
                    offsets,
                    draw_list,
                    landmarks["right_eyebrow_xy"],
                    imgui.get_color_u32(imgui.ImVec4(1, 0, 0, 1)),
                )
        imgui.end()

    def draw_outputs(self, outputs):
        if imgui.begin("Output Window")[0]:
            if outputs is None:
                imgui.text("No Output Data Available")
            else:
                for result in outputs:
                    imgui.text(result["id"])
                    imgui.same_line()
                    imgui.text(f"{result["value"]:.3f}")
        imgui.end()

    def draw_blendshapes(self, blendshapes):
        if imgui.begin("Blendshape Window")[0]:
            style_color = imgui.ImVec4(0.6, 0.0, 0.4, 1.0)
            imgui.push_style_color(imgui.Col_.plot_histogram, style_color)
            if blendshapes is None:
                imgui.text("No Blendshape Results Available")
            else:
                for blendshape_name in blendshapes:
                    imgui.progress_bar(
                        blendshapes[blendshape_name], overlay=blendshape_name
                    )
            imgui.pop_style_color()
        imgui.end()

    def draw_base_parameter_group(self, parameter: BaseParameter):
        imgui.text(f"Output: {parameter.output_id}")
        _, parameter.scale = imgui.input_float(
            f"{parameter.name} Scale: ", parameter.scale
        )
        _, parameter.offset = imgui.input_float(
            f"{parameter.name} Offset: ", parameter.offset
        )
        _, parameter.clamp = imgui.checkbox(
            f"{parameter.name} Clamp", parameter.clamp
        )
        if parameter.clamp:
            changed_min, new_min = imgui.input_float(
                f"{parameter.name} Min: ", parameter.min_val
            )
            changed_max, new_max = imgui.input_float(
                f"{parameter.name} Max: ", parameter.max_val
            )
            # Enforce min/max
            if changed_min:
                parameter.min_val = min(new_min, parameter.max_val)
            if changed_max:
                parameter.max_val = max(new_max, parameter.min_val)

    def draw_blendshape_group(self, blendshape_param: BlendshapeParameter):
        expanded = imgui.collapsing_header(
            f"Blendshape Calculation: {blendshape_param.name}"
        )
        if expanded:
            imgui.begin_group()
            self.draw_base_parameter_group(blendshape_param)

            with imgui.begin_table("Input Blendshapes", 2):
                imgui.table_setup_column("Parameter")
                imgui.table_setup_column("Sign")
                imgui.table_headers_row()
                for input_param in blendshape_param.input_parameters:
                    imgui.table_next_column()
                    imgui.text(input_param.name)
                    imgui.table_next_column()
                    sign_text = ""
                    if input_param.sign > 0:
                        sign_text = "Max_Positive"
                    else:
                        sign_text = "Max Negative"
                    imgui.text(sign_text)
            imgui.end_group()

    def draw_landmark_group(self, landmark_param: LandmarkParameter):
        expanded = imgui.collapsing_header(
            f"Landmark Calculation: {landmark_param.name}"
        )
        if expanded:
            imgui.begin_group()
            imgui.text(f"Landmark Calculation: {landmark_param.name}")
            self.draw_base_parameter_group(landmark_param)

            imgui.text(f"Input Set: {landmark_param.input_landmark_set}")
            option_name = LandmarkCalculateOption(
                landmark_param.calculate_option
            ).name
            imgui.text(f"Calculation: {option_name}")
            imgui.end_group()

    def draw_parameter_window(
        self, configs: ParameterConfigs, computer: ParameterComputer
    ):
        if imgui.begin("Parameter Window")[0]:
            parameter: Parameter
            for parameter in configs.parameters:
                match parameter.parameter_type:
                    case ParameterType.BLENDSHAPE:
                        self.draw_blendshape_group(parameter.parameter)
                    case ParameterType.LANDMARK:
                        self.draw_landmark_group(parameter.parameter)
                imgui.separator()

            if imgui.button("reset"):
                configs.config_reset()
            if imgui.button("set defaults"):
                configs.config_defaults()
            if imgui.button("save"):
                configs.file_save()

            if imgui.button("calibrate face position") and (
                results := computer.get_results()
            ):
                output = results.output_dict
                curr_pos_of = computer.parameter_configs.face_position_offset
                curr_rot_of = computer.parameter_configs.face_rotation_offset
                configs.face_position_offset = (
                    output.get("FacePositionX", 0) + curr_pos_of[0],
                    output.get("FacePositionY", 0) + curr_pos_of[1],
                    output.get("FacePositionZ", 0) + curr_pos_of[2],
                )
                configs.face_rotation_offset = (
                    output.get("FaceAngleX", 0) + curr_rot_of[0],
                    output.get("FaceAngleY", 0) + curr_rot_of[1],
                    output.get("FaceAngleZ", 0) + curr_rot_of[2],
                )
                configs.file_save()
        imgui.end()

    def keep_drawing(self):
        return not self.should_close


if __name__ == "__main__":
    computer = ParameterComputer()
    app = Application()
    while app.keep_drawing():
        app.render_frame(computer)
