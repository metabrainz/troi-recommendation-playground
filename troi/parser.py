#!/usr/bin/env python3

import re
import sys


TIME_RANGES = ["week", "month", "quarter", "half_yearly", "year", "all_time", "this_week", "this_month", "this_year"]
OPTIONS = ["easy", "hard", "medium", "and", "or", "nosim", "listened", "unlistened"] + TIME_RANGES
ELEMENTS = ["artist", "tag", "collection", "playlist", "stats", "recs"]

# TODO: Handle "rec:rob" better than artist(rec:rob)
#    Escape ( ) and ,

class ParseError(Exception):
    pass


class PromptParser:

    def __init__(self):
        self.element_check = re.compile(r"([a-zA-Z]+):")


    def identify_block(self, block):

        for element in ELEMENTS:
            if block.startswith(element + ":"):
                return element

        if block.startswith("#"):
            return "hashtag"

        # check for malformed element names
        m = self.element_check.match(block)
        if m is not None:
            raise ParseError("Unrecognized element name '%s'. Must be one of: %s" % (m.group(0), ",".join(ELEMENTS)))

        return "artistname"

    def parse_special_cases(self, prompt):

        block_type = self.identify_block(prompt)
        if block_type == "hashtag":
            return "tag:(%s)" % prompt[1:]
        if block_type == "artistname":
            return "artist:(%s)" % prompt

        return prompt

    def parse_query_into_blocks(self, prompt):

        blocks = []
        block = ""
        parens = 0
        escaped = False
        for i in range(len(prompt)):
            if not escaped and prompt[i] == '\\':
                escaped = True
                continue

            if escaped:
                if prompt[i] in ('(', ')', '\\'):
                    print("escaped ok")
                    escaped = False
                    block += prompt[i]
                    continue
                escaped = False

            if prompt[i] == '(':
                parens += 1
                block += prompt[i]
                continue

            if prompt[i] == ')':
                parens -= 1
                block += prompt[i]
                continue

            if prompt[i] == ' ' and parens == 0:
                if block == "":
                    continue

                blocks.append(block)
                block = ""

            if prompt[i] == ' ' and block == '':
                continue

            block += prompt[i]

        if block:
            blocks.append(block)

        return blocks

    def parse_block(self, block):

        opts = []
        weight = None

        name = self.identify_block(block)
        print(name)
        block = block[len(name) + 1:]

        if name in ("hashtag", "artistname"):
            raise ParseError("Unknown element '%s' at offset 1" % name)

        value = None
        text = ""
        parens = 0
        for i in range(len(block)):
            if block[i] == '(':
                if i > 0:
                    raise ParseError("() must start at the beginning of the value field.")
                parens += 1
                continue

            if block[i] == ')':
                parens -= 1
                if parens < 0:
                    raise ParseError("closing ) without matching opening ( near: '%s'. offset %d" % (block[i:], i + len(name) + 1))
                continue

            if block[i] == ':' and parens == 0 and value is None:
                value = text
                print("value: '%s'" % value)
                text = ""
                continue

            if block[i] == ':' and value is not None and weight is None:
                if not text:
                    weight = 1
                else:
                    # TODO: Add error checking
                    weight = int(text)

                opts = block[i+1:].split(",")
                if opts and opts[-1] == "":
                    raise ParseError("Trailing comma in options.")

                return name, value, weight, opts

            text += block[i]

        if parens > 0:
            raise ParseError("Missing closing ).")

        if parens < 0:
            raise ParseError("Missing opening (.")

        print(text)
        if value is None and text:
            value = text
            text = ""

        if weight is None:
            weight = 1

        if opts and opts[-1] == "":
            raise ParseError("Trailing comma in options.")

        return name, value, weight, opts


    def parse(self, prompt):

        """
        Portishead
        #pop

        artist:(portishead)
        tag:(trip hop)

        1. Break into list of elements

        """

        prompt = prompt.strip()
        prompt = self.parse_special_cases(prompt)
        blocks = self.parse_query_into_blocks(prompt)
        for block in blocks: 
            block = self.parse_special_cases(block)
            name, value, weight, opts = self.parse_block(block) 
            print("name: '%s'"% name)
            print("value: '%s'"% value)
            print("weight: '%s'"% weight)
            print("opts: '%s'"% opts)
            print()


pp = PromptParser()
pp.parse(sys.argv[1])
