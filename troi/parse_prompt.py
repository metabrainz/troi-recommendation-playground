import sys
from uuid import UUID

import pyparsing as pp
import pyparsing.exceptions

TIME_RANGES = ["week", "month", "quarter", "half_yearly", "year", "all_time", "this_week", "this_month", "this_year"]

OPTIONS = ["easy", "hard", "medium", "and", "or", "nosim", "listened", "unlistened"] + TIME_RANGES


class ParseError(Exception):
    pass


def build_parser():
    """ Build a parser using pyparsing, which is bloody brilliant! """

    # Define the entities and their keywords
    artist_element = pp.MatchFirst((pp.Keyword("artist"), pp.Keyword("a")))
    tag_element = pp.MatchFirst((pp.Keyword("tag"), pp.Keyword("t")))
    collection_element = pp.MatchFirst((pp.Keyword("collection")))
    playlist_element = pp.MatchFirst((pp.Keyword("playlist"), pp.Keyword("p")))
    stats_element = pp.MatchFirst((pp.Keyword("stats"), pp.Keyword("s")))
    recs_element = pp.MatchFirst((pp.Keyword("recs"), pp.Keyword("r")))

    # Define the various text fragments/identifiers that we plan to use
    text = pp.Word(pp.identbodychars + " ")
    uuid = pp.pyparsing_common.uuid()
    paren_text = pp.QuotedString("(", end_quote_char=")")
    tag_chars = pp.identbodychars + "&!-@$%^*=+;'"
    ws_tag = pp.OneOrMore(pp.Word(tag_chars + " "))
    tag = pp.Word(tag_chars)

    # Define supporting fragments that will be used multiple times
    paren_tag = pp.Suppress(pp.Literal("(")) \
              + pp.delimitedList(pp.Group(ws_tag, aslist=True), delim=",") \
              + pp.Suppress(pp.Literal(")"))
    weight = pp.Suppress(pp.Literal(':')) \
           + pp.Opt(pp.pyparsing_common.integer(), 1)
    opt_keywords = pp.MatchFirst([pp.Keyword(k) for k in OPTIONS])
    options = pp.Suppress(pp.Literal(':')) \
            + opt_keywords
    paren_options = pp.Suppress(pp.Literal(':')) \
                  + pp.Suppress(pp.Literal("(")) \
                  + pp.delimitedList(pp.Group(opt_keywords, aslist=True), delim=",") \
                  + pp.Suppress(pp.Literal(")"))
    optional = pp.Opt(weight + pp.Opt(pp.Group(options | paren_options), ""), 1)

    # Define artist element
    element_uuid = artist_element \
                 + pp.Suppress(pp.Literal(':')) \
                 + pp.Group(uuid, aslist=True) \
                 + optional
    element_paren_text = artist_element \
                       + pp.Suppress(pp.Literal(':')) \
                       + pp.Group(paren_text, aslist=True) \
                       + optional

    # Define tag element
    element_paren_tag = tag_element \
                      + pp.Suppress(pp.Literal(':')) \
                      + pp.Group(paren_text, aslist=True) \
                      + optional
    element_tag_shortcut = pp.Literal('#') \
                         + pp.Group(tag, aslist=True) \
                         + optional
    element_tag_paren_shortcut = pp.Literal('#') \
                               + pp.Group(paren_tag, aslist=True) \
                               + optional

    # Collection, playlist and stats, rec elements
    element_collection = collection_element \
                       + pp.Suppress(pp.Literal(':')) \
                       + pp.Group(uuid, aslist=True) \
                       + optional
    element_playlist = playlist_element \
                     + pp.Suppress(pp.Literal(':')) \
                     + pp.Group(uuid, aslist=True) \
                     + optional
    element_stats = stats_element \
                 + pp.Suppress(pp.Literal(':')) \
                 + pp.Opt(pp.Group(text, aslist=True), "") \
                 + optional
    element_paren_stats = stats_element \
                       + pp.Suppress(pp.Literal(':')) \
                       + pp.Group(paren_text, aslist=True) \
                       + optional
    element_recs = recs_element \
                 + pp.Suppress(pp.Literal(':')) \
                 + pp.Opt(pp.Group(text, aslist=True), "") \
                 + optional
    element_paren_recs = recs_element \
                       + pp.Suppress(pp.Literal(':')) \
                       + pp.Group(paren_text, aslist=True) \
                       + optional

    # Finally combine all elements into one, starting with the shortest/simplest elements and getting more
    # complex
    elements = element_tag_shortcut | element_uuid | element_paren_recs | element_collection | element_playlist | \
               element_paren_stats | element_paren_recs | element_recs | element_stats | \
               element_paren_text | element_paren_tag | element_tag_paren_shortcut

    # All of the above was to parse one single term, now allow the stats to define more than one if they want
    return pp.OneOrMore(pp.Group(elements, aslist=True))


def common_error_check(prompt: str):
    """ Pyparsing is amazing, but the error messages leave a lot to be desired. This function attempts
    to scan for common problems and give better error messages."""

    parts = prompt.split(":")
    try:
        if parts[2] in OPTIONS:
            sugg = f"{parts[0]}:{parts[1]}::{parts[2]}"
            raise ParseError("Syntax error: options specified in the weight field, since a : is missing. Did you mean '%s'?" % sugg)
    except IndexError:
        pass


def parse(prompt: str):
    """ Parse the given prompt. Return an array of dicts that contain the following keys:
          entity: str  e.g. "artist"
          value: list e.g. "57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"
          weight: int  e.g. 1 (positive integer)
          options: list e.g ["and", "easy"]

        raises ParseError if, well, a parse error is encountered. 
    """

    common_error_check(prompt)

    parser = build_parser()
    try:
        elements = parser.parseString(prompt.lower(), parseAll=True)
    except pp.exceptions.ParseException as err:
        raise ParseError(err)

    results = []
    for element in elements:
        if element[0] == "a":
            entity = "artist"
        elif element[0] == "s":
            entity = "stats"
        elif element[0] == "r":
            entity = "recs"
        elif element[0] == "t":
            entity = "tag"
        elif element[0] == "p":
            entity = "playlist"
        elif element[0] == "#":
            entity = "tag"
        else:
            entity = element[0]

        try:
            if entity == "tag" and element[1][0].find(",") > 0:
                element[1] = [s.strip() for s in element[1][0].split(",")]
        except IndexError:
            pass

        try:
            values = [UUID(element[1][0])]
        except (ValueError, AttributeError, IndexError):
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
