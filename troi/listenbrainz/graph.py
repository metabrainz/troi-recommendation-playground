import json

from troi import Element, Recording, PipelineError

import matplotlib.pyplot as plt
import numpy as np


class GraphUserRecordingRecommendationsElement(Element):


    def __init__(self, png_file, user_name):
        super().__init__()
        self.png_file = png_file
        self.user_name = user_name

    def inputs(self):
        return [Recording]

    def outputs(self):
        return [Recording]

    def read(self, inputs = []):

        rankings = []
        indexes = []
        for i, recording in enumerate(inputs[0]):
            rankings.append(recording.ranking)
            indexes.append(i)

        plt.plot(np.array(indexes), np.array(rankings))
        plt.title(f"Raw rec rankings for user {self.user_name}")
        plt.savefig(self.png_file)

        with open(f"rankings-{self.user_name}.json", "w") as f:
            f.write(json.dumps(rankings))

        return inputs[0]
