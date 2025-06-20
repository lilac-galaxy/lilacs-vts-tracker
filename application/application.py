from imgui.integrations.glfw import GlfwRenderer
import OpenGL.GL as gl
import glfw
import imgui

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
        self.window = self.impl_glfw_init()
        self.impl = GlfwRenderer(self.window)

    def __del__(self):
        self.impl.shutdown()
        glfw.terminate()

    def impl_glfw_init(self):
        width, height = 1280, 720
        window_name = "Lilac's VTS Face Tracker"

        if not glfw.init():
            raise Exception("Could not instantiate OpenGL context")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

        window = glfw.create_window(int(width), int(height), window_name, None, None)
        glfw.make_context_current(window)

        if not window:
            glfw.terminate()
            raise Exception("Count not instantiate Window")

        return window

    def render_frame(self, computer: ParameterComputer):
        glfw.poll_events()
        self.impl.process_inputs()

        imgui.new_frame()
        self.draw_windows(computer)

        gl.glClearColor(0.1, 0.0, 0.2, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        self.impl.render(imgui.get_draw_data())
        glfw.swap_buffers(self.window)

    def draw_windows(self, computer: ParameterComputer):
        self.draw_parameter_window(computer.parameter_configs)
        results = computer.get_results()
        blendshapes = None
        outputs = None
        landmarks = None
        if results != None:
            blendshapes = results.blendshapes
            outputs = results.outputs
            landmarks = results.landmarks

        self.draw_blendshapes(blendshapes)
        self.draw_outputs(outputs)
        self.draw_landmarks(landmarks)

    def draw_landmark_set(self, x, y, draw_list, landmarks, color):
        for point in landmarks:
            draw_list.add_circle_filled(
                x + ((0.5 - point[0])) * 1000,
                y + (point[1] - 0.5) * 1000,
                1,
                color,
            )

    def draw_landmarks(self, landmarks):
        with imgui.begin("Landmarks Window"):
            if landmarks == None:
                imgui.text("No Landmark Data Available")
            else:
                draw_list = imgui.get_window_draw_list()
                x, y = imgui.get_cursor_screen_pos()
                w_size_x, w_size_y = imgui.get_window_size()
                x += w_size_x // 2
                y += w_size_y // 2
                self.draw_landmark_set(
                    x,
                    y,
                    draw_list,
                    landmarks["all_xy"],
                    imgui.get_color_u32_rgba(1, 1, 0, 1),
                )
                self.draw_landmark_set(
                    x,
                    y,
                    draw_list,
                    landmarks["lips_xy"],
                    imgui.get_color_u32_rgba(1, 0, 0, 1),
                )
                self.draw_landmark_set(
                    x,
                    y,
                    draw_list,
                    landmarks["left_eye_xy"],
                    imgui.get_color_u32_rgba(1, 0, 0, 1),
                )
                self.draw_landmark_set(
                    x,
                    y,
                    draw_list,
                    landmarks["right_eye_xy"],
                    imgui.get_color_u32_rgba(1, 0, 0, 1),
                )
                self.draw_landmark_set(
                    x,
                    y,
                    draw_list,
                    landmarks["left_eyebrow_xy"],
                    imgui.get_color_u32_rgba(1, 0, 0, 1),
                )
                self.draw_landmark_set(
                    x,
                    y,
                    draw_list,
                    landmarks["right_eyebrow_xy"],
                    imgui.get_color_u32_rgba(1, 0, 0, 1),
                )

    def draw_outputs(self, outputs):
        with imgui.begin("Output Window"):
            if outputs == None:
                imgui.text("No Output Data Available")
            else:
                for result in outputs:
                    imgui.text(result["id"])
                    imgui.same_line()
                    imgui.text(f"{result["value"]:.3f}")

    def draw_blendshapes(self, blendshapes):
        with imgui.begin("Blendshape Window"):
            imgui.push_style_color(imgui.COLOR_PLOT_HISTOGRAM, 0.6, 0.0, 0.4)
            if blendshapes == None:
                imgui.text("No Blendshape Results Available")
            else:
                for blendshape_name in blendshapes:
                    imgui.progress_bar(
                        blendshapes[blendshape_name], overlay=blendshape_name
                    )
            imgui.pop_style_color()

    def draw_base_parameter_group(self, parameter: BaseParameter):
        imgui.text(f"Output: {parameter.output_id}")
        _, parameter.scale = imgui.input_float(
            f"{parameter.name} Scale: ", parameter.scale
        )
        _, parameter.offset = imgui.input_float(
            f"{parameter.name} Offset: ", parameter.offset
        )
        _, parameter.clamp = imgui.checkbox(f"{parameter.name} Clamp", parameter.clamp)
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
        expanded, _ = imgui.collapsing_header(
            f"Blendshape Calculation: {blendshape_param.name}"
        )
        if expanded:
            with imgui.begin_group():
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

    def draw_landmark_group(self, landmark_param: LandmarkParameter):
        expanded, _ = imgui.collapsing_header(
            f"Landmark Calculation: {landmark_param.name}"
        )
        if expanded:
            with imgui.begin_group():
                imgui.text(f"Landmark Calculation: {landmark_param.name}")
                self.draw_base_parameter_group(landmark_param)

                imgui.text(f"Input Set: {landmark_param.input_landmark_set}")
                option_name = LandmarkCalculateOption(
                    landmark_param.calculate_option
                ).name
                imgui.text(f"Calcuation: {option_name}")

    def draw_parameter_window(self, configs: ParameterConfigs):
        with imgui.begin("Parameter Window"):
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

    def keep_drawing(self):
        return not glfw.window_should_close(self.window)


if __name__ == "__main__":
    computer = ParameterComputer()
    app = Application()
    while app.keep_drawing():
        app.render_frame(computer)
