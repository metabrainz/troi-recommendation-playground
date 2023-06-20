#!/usr/bin/env python3

import sys
from uuid import UUID

# EXAMPLES
#
# a:05319f96-e409-4199-b94f-3cabe7cc188a
# artist:05319f96-e409-4199-b94f-3cabe7cc188a
#
# r:23f140b6-c017-4c04-9f48-cf0f3f376950
# recording:23f140b6-c017-4c04-9f48-cf0f3f376950
#
# rl:bb9c4738-6b94-49a3-9021-d21db849f818
# release:bb9c4738-6b94-49a3-9021-d21db849f818
#
# rg:d489a1fd-06b9-4611-b3f1-a19fccc80222
# release-group:d489a1fd-06b9-4611-b3f1-a19fccc80222
#
# g:76d79cc8-2995-4005-b266-7254fd9aaba4
# genre:76d79cc8-2995-4005-b266-7254fd9aaba4
#
# c:94207bbb-a877-4213-a8b1-92213226805e
# country:94207bbb-a877-4213-a8b1-92213226805e
# area:94207bbb-a877-4213-a8b1-92213226805e
#
# t:rock
# tag:rock
#
# t:"trip hop"
# tag-or:(rock pop):
#
# #rock
#
# y:1986
# year: 1986
#
# years:1986-2000
#
# TODO: Fix tag parsing: MB comma separates!
# improve error for "a: <mbid>"

PREFIXES = {
    "a": "artist",
    "ar": "area",
    "c": "country",
    "r": "recording",
    "rl": "release",
    "rg": "release-group",
    "g": "genre",
    "c": "country",
    "t": "tag",
    "to": "tag-or",
    "y": "year",
    "ys": "years"
}

UUID_VALUES = ("artist", "recording", "release-group", "genre", "country")


class ParseError(Exception):
    pass


def lex(prompt: str):
    """ Given a string, return the space separated tokens, taking care to mind quotes. """

    quote = 0
    token = ""
    tokens = []

    prompt = prompt.replace("\n\r\t", "").lower()
    prompt = " ".join(prompt.split())
    for ch in prompt.strip():
        if ch in (":", "(", ")"):
            if len(token) > 0:
                tokens.append(token.strip())
                token = ""

            tokens.append(ch)
            continue

        if ch == "#" and len(token) == 0:
            tokens.extend(("tag", ":"))
            continue

        if ch == " " and quote == 0 and len(token) > 0:
            tokens.append(token.strip())
            token = ""
            continue

        if ch == '"':
            if quote == 0:
                quote = 1
                continue

            quote = 0
            if len(token) > 0:
                tokens.append(token.strip())
                token = ""
                continue

        token += ch

    if quote != 0:
        raise ParseError('Missing closing "')

    if len(token) > 0:
        tokens.append(token.strip())

    return tokens


def sanity_check_field(entity: str, values: list, weight: str):
    """ Sanity check the given element data. If an error is found, raises ParseError().
        returns the value list passed in, possibly modified (number strings converted to ints) """

    def check_year(year):
        try:
            year = int(year)
        except ValueError:
            raise ParseError("Invalid year %s" % year)

        if year < 1800 or year > 2100:  # fuck the future
            raise ParseError("Invalid year %s. Must be between 1800 - 2100." % year)

        return year

    if entity == "year":
        values[0] = check_year(values[0])

    if entity == "years":
        try:
            from_year, to_year = values[0].split("-")
        except ValueError:
            raise ParseError("Year range must be in format YYYY-YYYY")

        values = [check_year(from_year), check_year(to_year)]

    if weight is not None:
        try:
            weight = int(weight)
        except ValueError:
            raise ParseError("Weight must be a positive, non-zero integer")

        if weight < 0 or weight > 1000:
            raise ParseError("Weight must be between 1 and 1000")

    return values, weight


def parse(prompt: str):
    """ Parse the given prompt. Return an array of dicts that contain the following keys:
          entity: str  e.g. "artist"
          values: list e.g. "57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"
          weight: int  e.g. 1 (positive integer)

        raises ParseError if, well, a parse error is encountered. 
    """

    prefix = None
    values = []
    suffix = None
    elements = []
    colons = 0
    parens = 0

    print(f"in parse '{prompt}'")

    for token in lex(prompt):

        if token == "(":
            if colons != 1:
                raise ParseError(": not allowed here")

            if parens != 0:
                raise ParseError("More than one ( now allowed per element")

            parens = 1
            continue

        if token == ")":
            if parens > 1:
                raise ParseError("More than one ) now allowed per element")

            if parens == 0:
                raise ParseError(") is missing (")

            parens = 0
            continue

        if token == ":":
            if parens == 1:
                raise ParseError("Missing ) before :")

            colons += 1
            continue

        # Check text token to see if prefix, value or suffix
        if colons == 0 and token not in list(PREFIXES) + list(PREFIXES.values()):
            raise ParseError(
                f'"{token}" is invalid. It must be one of the following prefixes: {",".join(list(PREFIXES.keys()) + list(PREFIXES.values()))}'
            )

        if token in PREFIXES:
            new_prefix = PREFIXES[token]
        elif token in PREFIXES.values():
            new_prefix = token
        else:
            new_prefix = None

        if new_prefix is None and prefix is not None and parens == 0 and len(values) > 0 and colons < 2:
            raise ParseError(f"Invalid prefix {token}")

        if new_prefix is not None:
            if prefix is not None:
                values, suffix = sanity_check_field(prefix, values, suffix)
                elements.append({"entity": prefix, "values": values, "weight": suffix})

            prefix = new_prefix
            values = []
            suffix = None
            colons = 0
            continue

        if colons == 2:
            suffix = token
            continue

        if colons == 1 and new_prefix is None:
            if parens == 1 or len(values) == 0:
                values.append(token)
                continue

    if parens != 0:
        raise ParseError("( not closed.")

    if prefix is not None and len(values) > 0:
        values, suffix = sanity_check_field(prefix, values, suffix)
        elements.append({"entity": prefix, "values": values, "weight": suffix})

    return elements
