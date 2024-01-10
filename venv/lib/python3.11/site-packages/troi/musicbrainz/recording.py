from troi import Element, Recording


class RecordingListElement(Element):
    """
        This element is used to pass a provided list of Recordings into the pipeline.

        :param recordings: The recordings to return from this Element.
    """

    def __init__(self, recordings):
        super().__init__()
        self.recordings = recordings

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):
        return self.recordings
