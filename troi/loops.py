import logging
from copy import copy

import troi
from troi import PipelineError, User
from troi.utils import discover_patches

logger = logging.getLogger(__name__)


class ForLoopElement(troi.Element):
    '''
        An element that receives items from a pipeline and for each item in the pipeline it instantiates a new patch and executes that patch. A normal use case might include taking a list of users and running the specified patch for each user.

        As of right now, only User objects can be processed with this element.

        :param patch_slug: the slug of the patch to run inside the for loop
        :param pipeline_args: the arguments passed to top-level pipeline, so that they apply to dynamically created pipelines inside the for loop
    '''

    def __init__(self, patch_slugs, patch_args):
        super().__init__()
        self.patch_slugs = patch_slugs
        self.patch_args = patch_args

    @staticmethod
    def inputs():
        return [User]

    @staticmethod
    def outputs():
        return []

    def read(self, inputs):

        patches = discover_patches()

        outputs = []
        for patch_slug in self.patch_slugs:
            if not patch_slug in patches:
                raise PipelineError("ForLoop: Cannot load patch '%s'" % patch_slug)

            patch = patches[patch_slug](False)
            for user in inputs[0]:
                args = copy(self.patch_args)
                args["user_name"] = user.user_name
                pipeline = patch.create(args)
                self.patch_args["created_for"] = user.user_name

                try:
                    logger.info("generate %s for %s" % (patch_slug, user.user_name))
                    playlist = troi.playlist.PlaylistElement()
                    playlist.set_sources(pipeline)
                    playlist.generate()

                    if self.patch_args["min_recordings"] is not None and \
                        len(playlist.playlists[0].recordings) < self.patch_args["min_recordings"]:
                        logger.info("Playlist does not have at least %d recordings, not submitting.\n" % self.patch_args["min_recordings"])
                        continue

                    if not self.patch_args["quiet"]:
                        playlist.print()
                    playlist.add_metadata({"algorithm_metadata": {"source_patch": patch_slug}})
                    if self.patch_args["upload"]:
                        if not self.patch_args["token"] or self.patch_args["token"] == "":
                            raise PipelineError("In order to upload a playlist an auth token must be provided. Use --token")

                        try:
                            if self.patch_args["created_for"] and self.patch_args["created_for"] != "":
                                playlist.submit(self.patch_args["token"], self.patch_args["created_for"])
                            else:
                                playlist.submit(self.patch_args["token"])
                        except troi.PipelineError as err:
                            logger.error("Failed to submit playlist: %s, continuing..." % err)
                            continue

                    outputs.append(playlist.playlists[0])
                    logger.info("")
                except troi.PipelineError as err:
                    logger.info("Failed to generate playlist: %s" % err)
                    raise

        # Return None if you want to stop processing this pipeline
        return outputs
