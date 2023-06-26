#!/usr/bin/env python3

import sys
from uuid import UUID

import pyparsing as pp
import pyparsing.exceptions

OPTIONS = ["easy", "hard", "medium", "and", "or"]

class ParseError(Exception):
    pass


def build_parser():
    """ Build a parser using pyparsing, which is bloody brilliant! """

    artist_element = pp.MatchFirst((pp.Keyword("artist"), pp.Keyword("a")))
    tag_element = pp.MatchFirst((pp.Keyword("tag"), pp.Keyword("t")))

    text = pp.Word(pp.alphanums)
    uuid = pp.pyparsing_common.uuid()
    paren_text = pp.QuotedString("(", end_quote_char=")")
    tag = pp.OneOrMore(pp.Word(pp.srange("[a-zA-Z0-9-_ ]")))
    stag = pp.OneOrMore(pp.Word(pp.srange("[a-zA-Z0-9-_]")))
    paren_tag = pp.Suppress(pp.Literal("(")) + pp.delimitedList(pp.Group(tag, aslist=True), delim=",") + pp.Suppress(
        pp.Literal(")"))

    weight = pp.Suppress(pp.Literal(':')) + pp.pyparsing_common.integer()
    opt_keywords = pp.Keyword("and") | pp.Keyword("or") | pp.Keyword("easy") | pp.Keyword("medium") | pp.Keyword("hard")
    options = pp.Suppress(pp.Literal(':')) + opt_keywords
    paren_options = pp.Suppress(pp.Literal(':')) + pp.Suppress(pp.Literal("(")) + pp.delimitedList(
        pp.Group(opt_keywords, aslist=True), delim=",") + pp.Suppress(pp.Literal(")"))
    optional = pp.Opt(weight + pp.Opt(pp.Group(options | paren_options), ""), 1)

    element_uuid = artist_element + pp.Suppress(pp.Literal(':')) + pp.Group(uuid, aslist=True) + optional
    element_text = artist_element + pp.Suppress(pp.Literal(':')) + pp.Group(text, aslist=True) + optional
    element_paren_text = artist_element + pp.Suppress(pp.Literal(':')) + pp.Group(paren_text, aslist=True) + optional

    element_tag = tag_element + pp.Suppress(pp.Literal(':')) + pp.Group(text, aslist=True) + optional
    element_paren_tag = tag_element + pp.Suppress(pp.Literal(':')) + pp.Group(paren_tag, aslist=True) + optional
    element_tag_shortcut = pp.Literal('#') + pp.Group(stag, aslist=True) + optional
    element_tag_paren_shortcut = pp.Literal('#') + pp.Group(paren_tag, aslist=True) + optional

    element = element_uuid | element_text | element_paren_text | element_tag | element_paren_tag \
            | element_tag_shortcut | element_tag_paren_shortcut

    return pp.OneOrMore(pp.Group(element, aslist=True))


def parse(prompt: str):
    """ Parse the given prompt. Return an array of dicts that contain the following keys:
          entity: str  e.g. "artist"
          value: list e.g. "57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"
          weight: int  e.g. 1 (positive integer)
          options: list e.g ["and", "easy"]

        raises ParseError if, well, a parse error is encountered. 
    """

    parser = build_parser()
    try:
        elements = parser.parseString(prompt, parseAll=True)
    except pp.exceptions.ParseException as err:
        raise ParseError(err)

    results = []
    for element in elements:
        if element[0] == "a":
            entity = "artist"
        elif element[0] == "t":
            entity = "tag"
        elif element[0] == "#":
            entity = "tag"
        else:
            entity = element[0]

        try:
            values = [ UUID(element[1][0]) ]
        except (ValueError, AttributeError):
            values = []
            for value in element[1]:
                if isinstance(value, list):
                    values.append(value[0])
                else:
                    values.append(value)

        try:
            weight = element[2]
        except IndexError:
            weight = 1

        opts = []
        try:
            for opt in element[3]:
                if isinstance(opt, list):
                    opts.append(opt[0])
                else:
                    opts.append(opt)
        except IndexError:
            pass

        results.append({"entity": entity, "values": values, "weight": weight, "opts": opts})

    return results


if __name__ == "__main__":
    parse("artist:ff2e249b-b64a-445a-9cd0-d655cff573c2:2:(and)")
    parse("artist:ff2e249b-b64a-445a-9cd0-d655cff573c2")
    parse("artist:ff2e249b-b64a-445a-9cd0-d655cff573c2:2")
    parse("artist:ff2e249b-b64a-445a-9cd0-d655cff573c2:2:and")
    parse("artist:ff2e249b-b64a-445a-9cd0-d655cff573c2:2:or")
    parse("artist:ff2e249b-b64a-445a-9cd0-d655cff573c2:2:(and,easy)")
    parse("artist:(artist name)")
    parse("tag:rock:2:and")
    parse("tag:rock")
    parse("tag:(rock)")
    parse("#rock")
    parse("#(rock)")
    parse("#(trip hop)")
    parse("#(rock,pop)")
    parse("#(rock,pop):3")
    parse("#(rock,pop):2:easy")
    parse("#(rock,pop):2:(easy,and)")
    parse("#(rock,pop):2:(easy)")
    parse("#(rock,pop):2:medium #rock")
