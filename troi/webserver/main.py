from collections import defaultdict
import copy
import json
import os
import sys
import traceback
import requests.exceptions

from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import NotFound, BadRequest, InternalServerError, \
                                MethodNotAllowed, ImATeapot, ServiceUnavailable
import troi.utils
import troi.playlist

TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "template")
PATCH_FOLDER = "/app/patches"

sys.stderr.write(TEMPLATE_FOLDER + "\n")

registered_queries = {}
app = Flask(__name__,
            template_folder = TEMPLATE_FOLDER)

@app.route('/')
def index():
    """ The home page that shows all of the available queries."""
    return render_template("index.html", patches=patches)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Patch not found."), 404


def error_check_arguments(inputs):

    args = []
    for input in inputs:
        arg = request.args.get(input['name'], '')
        if not arg and not input['optional']:
            return "Parameter %s is missing." % input['name'], ()
        try:
            args.append(input['type'](arg))
        except:
            if input['optional']:
                args.append(None)
            else:
                return "Parameter %s is of incorrect type. Must be %s." % (input['name'], input['type']), ()
                

    return "", args


def web_patch_handler():
    """
        This is the view handler for the web page.
    """
  
    patch_name = request.path[1:]
    try:
        patch = patches[patch_name]()
    except KeyError:
        return render_template("error.html", error="Cannot load patch %s" % patch_name), 404

    inputs = patch.inputs()
    outputs = patch.outputs()
    desc = patch.description()

    recordings = []
    post_data = ""
    error = ""
    args = []
    if len(request.args):
        error, args = error_check_arguments(inputs)
        if not error:
            try:
                pipeline = patch.create(args)
            except (BadRequest, InternalServerError, ImATeapot, ServiceUnavailable, NotFound, RuntimeError, requests.exceptions.HTTPError) as err:
                error = err
            except PipelineError as err:
                error = err
            except Exception as err:
                error = traceback.format_exc()
                print(error)

            if not error:
                try:
                    playlist = troi.playlist.PlaylistElement()
                    playlist.set_sources(pipeline)
                    playlist.generate()
                    recordings = playlist.recordings
                    post_data = playlist.playlist
                except (RuntimeError, requests.exceptions.HTTPError) as err:
                    error = str(err)

    return render_template("patch.html",
                           error=error,
                           recordings=recordings,
                           count=len(recordings) if recordings else -1,
                           inputs=inputs,
                           columns=outputs,
                           args=args,
                           desc=desc,
                           slug=patch_name,
                           post_data=post_data)

patches = troi.utils.discover_patches(PATCH_FOLDER)
for patch in patches:
    slug = patches[patch]().slug()
    app.add_url_rule('/%s' % slug, slug, web_patch_handler)
