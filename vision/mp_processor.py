import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class MPProcessor:
    def __init__(self, use_gpu: bool, model: str, result_callback):
        delagate = python.BaseOptions.Delegate.CPU
        if use_gpu:
            delagate = python.BaseOptions.Delegate.GPU

        base_options = python.BaseOptions(model_asset_path=model, delegate=delagate)

        self.result_callback = result_callback

        options = vision.FaceLandmarkerOptions(
            base_options,
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=1,
            result_callback=self.process_results,
        )

        self.detector = vision.FaceLandmarker.create_from_options(options)

    def detect_image(self, input_image, timestamp):
        formatted_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=input_image)
        self.detector.detect_async(formatted_image, timestamp)

    def process_results(
        self,
        detection_result,
        _: mp.Image,
        timestamp_ms: int,
    ):
        self.result_callback(detection_result, timestamp_ms)
