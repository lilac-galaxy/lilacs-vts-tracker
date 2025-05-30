from computation.landmark_sets import LANDMARK_SETS


class LandmarkParser:
    def __init__(self, landmarks):
        self.landmark_sets = {}
        self.landmark_sets["all_xy"] = []
        self.landmark_sets["all_xyz"] = []
        for landmark_set_name in LANDMARK_SETS:
            self.landmark_sets[landmark_set_name + "_xy"] = []
            self.landmark_sets[landmark_set_name + "_xyz"] = []
        self.read_landmarks(landmarks)

    def read_landmarks(self, landmarks):
        for idx in range(len(landmarks)):
            landmark = landmarks[idx]
            for landmark_set_name in LANDMARK_SETS:
                if idx in LANDMARK_SETS[landmark_set_name]:
                    self.landmark_sets[landmark_set_name + "_xy"].append(
                        (landmark.x, landmark.y)
                    )
                    self.landmark_sets[landmark_set_name + "_xyz"].append(
                        [landmark.x, landmark.y, landmark.z]
                    )
                self.landmark_sets["all_xy"].append((landmark.x, landmark.y))
                self.landmark_sets["all_xyz"].append(
                    [landmark.x, landmark.y, landmark.z]
                )

    def get_landmark_sets(self):
        return self.landmark_sets
