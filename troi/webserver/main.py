from collections import defaultdict
import copy
import json
import os
import sys
import traceback

from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import NotFound, BadRequest, InternalServerError, \
                                MethodNotAllowed, ImATeapot, ServiceUnavailable
import troi.utils

TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "template")
PATCH_FOLDER = "/app/patches"

sys.stderr.write(TEMPLATE_FOLDER + "\n")

registered_queries = {}
app = Flask(__name__,
            template_folder = TEMPLATE_FOLDER)


patches = troi.utils.discover_patches(PATCH_FOLDER)
print("Loaded %d patches from %s" % (len(patches), PATCH_FOLDER))

@app.route('/')
def index():
    """ The home page that shows all of the available queries."""
    return render_template("index.html", patches=patches)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Patch not found."), 404


def convert_http_args_to_json(inputs, req_args):
    """
        THis function converts a series of HTTP arguments into a sane JSON (dict)
        that mimicks the data that is passed to the POST function. Also does
        some error checking on the data. Returns a complete dict or parameters 
        and a blank string or None and an error string.
    """

    args = {}
    num_args = 0
    list_len = -1
    for arg in req_args:
        args[arg] = req_args[arg].split(",")
        num_args = len(args[arg])
        list_len = max(list_len, len(args[arg]))

    singletons = {}
    for arg in args:
        if arg.startswith("[") and len(args[arg]) != list_len:
            return [], "Lists passed as parameters must all be the same length."

        if len(args[arg]) == 1:
            singletons[arg] = args[arg][0]

    arg_list = []
    try:
        for i in range(list_len):
            row = copy.deepcopy(singletons)
            for input in inputs:
                if input not in args:
                    return [], "Missing parameter '%s'." % input
                if input not in singletons:
                    row[input] = args[input][i]
            arg_list.append(row)
    except KeyError as err:
        return [], "KeyError: " + str(err)

    return arg_list, ""


def error_check_arguments(inputs, req_json):
    """
        Given the JSON (dict) version of the parameters, ensure that they are sane.
        Parameters must all be available for each row and parameters cannot be blank.
        If there are parameters that are lists, make sure all lists contain
        the same number of elements. Returns error string if error, otherwise empty string
    """

    if not req_json:
        return "No parameters supplied. Required: %s" % (",".join(inputs))

    for i, row in enumerate(req_json):
        for input in inputs:
            if not input in row:
                return "Required parameter '%s' missing in row %d." % (input, i)
            if not row[input]:
                return "Required parameter '%s' cannot be blank in row %d." % (input, i)

    # Examine one row to ensure that all the parameters are there.
    for req in req_json[0]:
        if req not in inputs:
            return "Too many parameters passed. Extra: '%s'" % req

    return ""


def web_patch_handler():
    """
        This is the view handler for the web page.
    """
  
    patch_name = request.path
    try:
        patch = patches[patch]()
    except KeyError:
        return render_template("error.html", error="Cannot load patch %s" % patch_name), 404

    inputs = patch.inputs()
    outputs = patch.outputs()

    recordings = []
    arg_list, error = convert_http_args_to_json(inputs, request.args)
    if error:
        return render_template("error.html", error=error)

    if arg_list:
        error = error_check_arguments(inputs, arg_list)
        if not error:
            
            if arg_list:
                json_post = json.dumps(arg_list, indent=4, sort_keys=True)

            try:
                pipeline = patch.create(checked_args)
            except (BadRequest, InternalServerError, ImATeapot, ServiceUnavailable, NotFound) as err:
                error = err
            except Exception as err:
                error = traceback.format_exc()
                print(error)

            playlist = troi.playlist.PlaylistElement()
            playlist.set_sources(pipeline)
            playlist.generate()


    return render_template("patch.html",
                           error=error,
                           recordings=playlist.recordings,
                           count=len(recordings) if recordings else -1,
                           inputs=inputs,
                           columns=outputs,
                           args=request.args,
                           desc=desc,
                           slug=patch_name)
