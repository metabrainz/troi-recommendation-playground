#!/usr/bin/env python3

import sys

import pyparsing as pp
from icecream import ic

OPTIONS = ["easy", "hard", "medium", "and", "or"]


def build_parser():

    artist_element = pp.MatchFirst((pp.Keyword("artist"), pp.Keyword("a")))
    tag_element = pp.MatchFirst((pp.Keyword("tag"), pp.Keyword("t")))

    text = pp.Word(pp.alphanums)
    uuid = pp.pyparsing_common.uuid()
    paren_text = pp.QuotedString("(", end_quote_char=")")
    tag = pp.OneOrMore(pp.Word(pp.alphanums))
    paren_tag = pp.Suppress(pp.Literal("(")) + pp.delimitedList(pp.Group(tag, aslist=True), delim=",") + pp.Suppress(
        pp.Literal(")"))

    weight = pp.Suppress(pp.Literal(':')) + pp.pyparsing_common.integer()
    opt_keywords = pp.Keyword("and") | pp.Keyword("or") | pp.Keyword("easy") | pp.Keyword("medium")
    options = pp.Suppress(pp.Literal(':')) + opt_keywords
    paren_options = pp.Suppress(pp.Literal(':')) + pp.Suppress(pp.Literal("(")) + pp.delimitedList(
        pp.Group(opt_keywords, aslist=True), delim=",") + pp.Suppress(pp.Literal(")"))
    optional = pp.Opt(weight + pp.Opt(options | paren_options, ""), 1)

    element_uuid = artist_element + pp.Suppress(pp.Literal(':')) + pp.Group(uuid, aslist=True) + optional
    element_text = artist_element + pp.Suppress(pp.Literal(':')) + pp.Group(text, aslist=True) + optional
    element_paren_text = artist_element + pp.Suppress(pp.Literal(':')) + pp.Group(paren_text, aslist=True) + optional

    element_tag = tag_element + pp.Suppress(pp.Literal(':')) + pp.Group(text, aslist=True) + optional
    element_paren_tag = tag_element + pp.Suppress(pp.Literal(':')) + pp.Group(paren_tag, aslist=True) + optional
    element_tag_shortcut = pp.Literal('#') + pp.Group(tag, aslist=True) + optional
    element_tag_paren_shortcut = pp.Literal('#') + pp.Group(paren_tag, aslist=True) + optional

    element = element_uuid | element_text | element_paren_text | element_tag | element_paren_tag \
            | element_tag_shortcut | element_tag_paren_shortcut

    return pp.OneOrMore(pp.Group(element, aslist=True))


def parse(prompt):

    parser = build_parser()
    print(prompt)
    parse_data = parser.parseString(prompt, parseAll=True)
    for data in parse_data:
        ic(data)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        parse(sys.argv[1])
    else:
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
        parse("#(rock pop)")
        parse("#(rock,pop)")
        parse("#(rock,pop):3")
        parse("#(rock,pop):2:easy")
        parse("#(rock,pop):2:(easy,and)")
        parse("#(rock,pop):2:(easy)")
        parse("#(rock,pop):2:medium #rock")
