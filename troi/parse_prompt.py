from uuid import UUID
import re

TIME_RANGES = ["week", "month", "quarter", "half_yearly", "year", "all_time", "this_week", "this_month", "this_year"]
ELEMENTS = ["artist", "tag", "collection", "playlist", "stats", "recs", "country"]

ELEMENT_OPTIONS = {
    "artist": ["nosim", "easy", "medium", "hard"],
    "tag": ["nosim", "and", "or", "easy", "medium", "hard"],
    "collection": ["easy", "medium", "hard"],
    "playlist": ["easy", "medium", "hard"],
    "stats": TIME_RANGES,
    "recs": ["easy", "medium", "hard", "listened", "unlistened"],
    "country": ["easy", "medium", "hard"]
}

OPTIONS = set()
for eo in ELEMENT_OPTIONS:
    OPTIONS.update(ELEMENT_OPTIONS[eo])

OPTIONS = list(OPTIONS)


class ParseError(Exception):
    pass


class PromptParser:
    """
    Parse the LB radio prompt and return a list of elements and all of their data/options
    """

    def __init__(self):
        self.clean_spaces = re.compile(r"\s+")
        self.element_check = re.compile(r"([a-zA-Z]+):")

    def identify_block(self, block):
        """Given a prompt string, identify the block that is at the beginning of the string"""

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
        """Detect the artist and tag special cases and re-write the query in long hand form."""

        block_type = self.identify_block(prompt)
        if block_type == "hashtag":
            return "tag:(%s)" % prompt[1:]
        if block_type == "artistname":
            return "artist:(%s)" % prompt

        return prompt

    def set_block_values(self, name, values, weight, opts, text, block):
        """Parse, process and sanity check data for an element"""

        if values is None:
            if name in ("artist", "country", "collection", "playlist"):
                try:
                    values = [UUID(text)]
                except ValueError:
                    values = [text]
            elif name == "tag":
                values = text.split(",")
                values = [v.strip() for v in values]
            else:
                values = [text]
        elif weight is None:
            if not text:
                weight = 1
            else:
                try:
                    weight = int(text)
                except ValueError:
                    raise ParseError("Weight must be a positive integer, not '%s'" % text)
        elif not opts:
            opts = text.split(",")
            if opts and opts[-1] == "":
                raise ParseError("Trailing comma in options.")

        return values, weight, opts

    def parse(self, prompt):
        """Parse an actual LB-radio prompt and return a list of [name, [values], weight, [opts]]"""

        prompt = self.clean_spaces.sub(" ", prompt).strip()
        block = self.parse_special_cases(prompt)
        blocks = []
        while True:
            name = ""
            for element in ELEMENTS:
                if block.startswith(element + ":"):
                    name = element
                    break
            if not name:
                raise ParseError("Unknown element '%s'" % block)

            block = block[len(name):]
            if block[0] == ':':
                block = block[1:]

            opts = []
            weight = None
            values = None
            text = ""
            parens = 0
            escaped = False
            for i in range(len(block)):
                if not escaped and block[i] == '\\':
                    escaped = True
                    continue

                if escaped:
                    if block[i] in ('(', ')', '\\'):
                        escaped = False
                        text += block[i]
                        continue
                    escaped = False

                if block[i] == '(':
                    if i > 0:
                        raise ParseError("() must start at the beginning of the value field.")
                    parens += 1
                    continue

                if block[i] == ')':
                    parens -= 1
                    if parens < 0:
                        raise ParseError("closing ) without matching opening ( near: '%s'." % block[i:])
                    continue

                if block[i] == ':' and parens == 0:
                    values, weight, opts = self.set_block_values(name, values, weight, opts, text, block)
                    text = ""
                    continue

                # Check to make sure that some values are in ()
                if name in ("artist", "country", "collection", "playlist") and i == 0 and not block[i] == "(":
                    raise ParseError("Element value must be enclosed in ( ). Try: %s:(name)" % (name))

                if block[i] == ' ' and parens == 0:
                    break

                text += block[i]

            # Now that we've parsed a block, do some sanity checking
            values, weight, opts = self.set_block_values(name, values, weight, opts, text, block)
            try:
                block = block[i + 1:]
            except UnboundLocalError:
                raise ParseError("incomplete prompt")

            if parens > 0:
                raise ParseError("Missing closing ).")

            if parens < 0:
                raise ParseError("Missing opening (.")

            for opt in opts:
                if opt not in ELEMENT_OPTIONS[name]:
                    raise ParseError("Option '%s' is not allowed for element %s" % (opt, name))

            blocks.append({"entity": name, "values": values, "weight": weight or 1, "opts": opts})

            if len(block) == 0:
                break

        return blocks
