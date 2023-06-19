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
#
# #rock
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
        if ch in (":", "(", ")"):
            if len(token) > 0:
                tokens.append(token.strip())
                token = ""

            tokens.append(ch)
            continue

        if ch  == " " and quote == 0 and len(token) > 0:
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

def yacc(prompt: str):

    prefix = ""
    values = []
    suffix = ""
    elements = []
    last_token = None
    colons = 0
    parens = 0
  
    for token in lex(prompt):
        print(f"\ntoken '{token}', prefix: '{prefix}' values '{values}' suffix: '{suffix}' colons: {colons}")

        if token == "(":
            if colons != 1:
                return [], ": not allowed here"

            if parens != 0:
                return [], "() may not be nested"

            parens = 1
            continue

        if token == ")":
            if colons != 1:
                return [], ": not allowed here"

            if parens != 1:
                return [], "() may not be nested"

            parens = 0
            continue

        if token == ":":
            colons += 1
            continue

        # Check text token to see if prefix, value or suffix
        if colons == 0 and token not in list(PREFIXES) + list(PREFIXES.values()):
            return [], f'"{token}" must have one of the following prefixes: {",".join(list(PREFIXES.keys()) + list(PREFIXES.values()))}'

        if token in PREFIXES:
            new_prefix = PREFIXES[token]
        elif token in PREFIXES.values():
            new_prefix = token
        else: 
            new_prefix = None

        if token not in ("and", "or") and colons == 2:
            return [], "Suffix must be 'and' or 'or'"
        else:
            suffix = token

        print(f"  new prefix: {new_prefix} suffix: {suffix}")
        if colons == 0 and new_prefix is not None:
            prefix = token
            continue

        if colons == 1 and new_prefix is None:
            values.append(token)
            continue

        if colons > 1:
            print(prefix, values, suffix)
            elements.append((prefix, values, suffix))
            prefix = token
            values = []
            suffix = None
            parens = 0
            colons = 0

        # Parse token shorthand
        if token[0] == '#':
            if len(token) == 0:
                return [], "#tags must have a name that is at least one character long."

            if parens != 0 or colons != 0:
                return [], "#tags may not contain : or other characters."

            prefix = "tag"
            values.append((prefix, token[1:], None))
            print(f"tag {token[1:]}")
            continue

    if prefix is not None and len(values) > 0:
        print(prefix, values, suffix)
        elements.append((prefix, values, suffix))

    return elements, ""



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

    prompt = 'artist:05319f96-e409-4199-b94f-3cabe7cc188a #downtempo tag:("trip hop" abstract):or c:d1ad6d63-448b-43c7-9de3-e60ac8418106 y:1996 ys:1986-2000'

    elements, err = yacc(" ".join(sys.argv[1:]))
    if err:
        print(err)
#    else:
#        for prefix, values, suffix in elements:
#            print(prefix, values, suffix)

    sys.exit(0)

    elements, err = parse_prompt(prompt)
    if err:
        print(f"Error: {err}")
    else:
        for prefix, value in elements:
            print("%-25s %s" % (prefix, value))
