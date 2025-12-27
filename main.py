import argparse
from vision.capture_device import CaptureDevice
from vision.mp_processor import MPProcessor
from communication.vtube_studio_interface import VTSInterface
from computation.compute_parameters import ParameterComputer
from websockets.exceptions import ConnectionClosedOK
from application.application import Application
import traceback
from threading import Thread


class ConnectionMonitor:
    def __init__(self):
        self.valid = True

    def connection_valid(self):
        return self.valid

    def connection_closed(self):
        print("Connection Closed, exiting!")
        self.valid = False


def get_args():
    parser = argparse.ArgumentParser(
        prog="lilacs-VTS-Face-Tracker",
        description="Plugin to compute customized VTube Studio parameters \
            from Google's Mediapipe face landmarker",
    )
    parser.add_argument(
        "-a",
        "--auth_file",
        help="json file containing vtube studio auth token",
        default="auth.json",
    )
    parser.add_argument(
        "-m",
        "--model",
        help="mediapipe model file",
        default="face_landmarker_v2_with_blendshapes.task",
    )
    parser.add_argument(
        "--address",
        help="API address for VTube Studio",
        default="ws://localhost:8001",
    )
    parser.add_argument(
        "-c", "--camera", type=int, help="index of camera device", default=0
    )
    parser.add_argument(
        "-W", "--width", type=int, help="width of camera image", default=1280
    )
    parser.add_argument(
        "-H", "--height", type=int, help="height of camera image", default=720
    )
    parser.add_argument(
        "-f", "--fps", type=int, help="frame rate of the camera", default=30
    )
    parser.add_argument("-g", "--use-gpu", default=False, action="store_true")
    parser.add_argument(
        "--run-offline",
        help="Run without connecting to VTube Studio",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--run-app",
        help="Launch GUI interface",
        default=False,
        action="store_true",
    )
    return parser.parse_args()


def main(args):
    # Init capture device
    capture = CaptureDevice(args.camera, args.width, args.height, args.fps)

    # Init Websocket Connection
    if args.run_offline is False:
        vts_interface = VTSInterface(args.address, args.auth_file)
    else:
        vts_interface = None

    # Connection Monitor for clean exiting
    connection_monitor = ConnectionMonitor()

    # Create computer
    parameter_computer = ParameterComputer(save_results=args.run_app)

    # Create application (if specified)
    if args.run_app:
        app = Application()

    # Init Mediapipe
    def callback(detection_results, timestamp):
        parameter_results = parameter_computer.compute_parameters(
            detection_results, timestamp
        )
        if args.run_offline is False:
            try:
                vts_interface.send_detection_parameter_results(
                    parameter_results
                )
            except ConnectionClosedOK:
                connection_monitor.connection_closed()

    processor = MPProcessor(args.use_gpu, args.model, callback)

    def _face_detection_loop():
        try:
            while connection_monitor.connection_valid():
                ret = capture.read_image()
                if ret.valid is not None:
                    processor.detect_image(ret.image, ret.timestamp)
                else:
                    capture.wait()
        except KeyboardInterrupt:
            print("Keyboard Interrupt, exiting.")
            connection_monitor.connection_closed()
        except Exception:
            traceback.print_exc()
            connection_monitor.connection_closed()

    if not args.run_app:
        _face_detection_loop()

    else:
        face_detection_thread = Thread(target=_face_detection_loop)
        face_detection_thread.start()
        # Main Loop
        try:
            while connection_monitor.connection_valid():
                # Display
                if app.keep_drawing():
                    app.render_frame(parameter_computer)
                else:
                    print("Window closed, quitting")
                    connection_monitor.connection_closed()
                    break
        except KeyboardInterrupt:
            print("Keyboard Interrupt, exiting.")
            connection_monitor.connection_closed()
        except Exception:
            traceback.print_exc()
            connection_monitor.connection_closed()

        face_detection_thread.join()


if __name__ == "__main__":
    args = get_args()
    main(args)
