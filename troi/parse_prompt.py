#!/usr/bin/env python3

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
#
# #rock
#
# rgt:rock
# release-group-tag:rock
# 
# y:1986
# year: 1986
# 
# years:1986-2000
#

PREFIXES = {
    "a": "artist",
    "r": "recording",
    "rl": "release",
    "rg": "release-group",
    "g": "genre",
    "c": "country",
    "t": "tag",
    "tag": "tag",
    "rgt": "release-group-tag",
    "release-group-tag": "release-group-tag",
    "y": "year",
    "ys": "years"
}

UUID_VALUES = ("artist", "recording", "release-group", "genre", "country")

def lex(prompt: str):
    """ Given a string, return the space separated token, taking care to mind quotes. """

    quote = 0
    token = ""
    tokens = []

    prompt = prompt.replace("\n\r\t", "").lower()
    prompt = " ".join(prompt.split())
    for ch in prompt.strip():
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

    if len(token) > 0:
        tokens.append(token.strip())

    return tokens


def parse_prompt(prompt: str):
    """ Lex the prompt, then parse out the correct elements and error check the prompt.
        return a list of tuples that contain (prefix, value). Value may be string, int or tuple.

        For instance:

        artist:05319f96-e409-4199-b94f-3cabe7cc188a and #downtempo rgt:"trip hop" c:d1ad6d63-448b-43c7-9de3-e60ac8418106 y:1996 ys:1986-2000

        returns:

        artist                    05319f96-e409-4199-b94f-3cabe7cc188a
        op                        and
        tag                       downtempo
        release-group-tag         trip hop
        country                   d1ad6d63-448b-43c7-9de3-e60ac8418106
        year                      1996
        years                     (1986, 2000)

    """

    elements = []
    for token in lex(prompt):
        if token in ("and", "or"):
            elements.append(("op", token))
            continue

        if token[0] == '#':
            if len(token) == 0:
                return {}, "#tags must have a name that is at least one character long."

            elements.append(("tag", token[1:]))
            continue

        if token.find(":") < 0 and token not in ("and", "or"):
            return {}, f'"{token}" is not a valid element. Elements must have a prefix and :, a #tag, or be one of "or" or "and"'

        try:
            prefix, value = token.split(":")
        except ValueError:
            return {}, f'"{token}" is not a valid element. Elements must have a prefix and :, a #tag, or be one of "or" or "and"'

        if prefix == "" or value == "":
            return {}, f'"{token}" is not a valid element. Elements must have a prefix and :, a #tag, or be one of "or" or "and"'

        if prefix not in list(PREFIXES) + list(PREFIXES.values()):
            return {}, f'"{token}" must have one of the following prefixes: {",".join(list(PREFIXES.keys()) + list(PREFIXES.values()))}'
        else:
            if prefix in PREFIXES:
                prefix = PREFIXES[prefix]

        if prefix not in PREFIXES.values():
            return {}, f'"{token}" must have one of the following prefixes: {",".join(list(PREFIXES.keys()) + list(PREFIXES.values()))}'

        if prefix in UUID_VALUES:
            try:
                u = UUID(value)
            except ValueError:
                return {}, f"{value} is not a valid MBID."

        if prefix == "year":
            try:
                year = int(value)
            except ValueError:
                return {}, "Year must be a 4 digit number"

            if year < 1900 or year > 2100: # Sometime will need to update this. eventually.
                return {}, "Year must be >= 1900 and <= 2100."

            value = year

        if prefix == "years":
            try:
                begin_year, end_year = value.split("-")
                begin_year = int(begin_year)
                end_year = int(end_year)
            except ValueError:
                return {}, "years element must have a format of YYYY-YYYY."

            if begin_year < 1900 or begin_year > 2100:
                return {}, "Begin year must be >= 1900 and <= 2100."

            if end_year < 1900 or end_year > 2100:
                return {}, "End year must be >= 1900 and <= 2100."

            value = (begin_year, end_year)

        elements.append((prefix, value))

    return elements, ""

if __name__ == "__main__":
    elements, err = parse_prompt('artist:05319f96-e409-4199-b94f-3cabe7cc188a and #downtempo rgt:"trip hop" c:d1ad6d63-448b-43c7-9de3-e60ac8418106 y:1996 ys:1986-2000')
    if err:
        print(f"Error: {err}")
    else:
        for prefix, value in elements:
            print("%-25s %s" % (prefix, value))
