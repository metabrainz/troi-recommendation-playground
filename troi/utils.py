from troi import Element, Artist, Release, Recording

def print_entity_list(entities, count=0):

    if count == 0:
        count = len(entities)

    if isinstance(entities[0], Artist): 
        print("artist list")
        for e in entities[:count]:
            print("  %s %s" % (e.mbid)[:5], e.name)
    elif isinstance(entities[0], Recording): 
        print("recording list")
        for e in entities[:count]:
            if e.artist:
                print("  %s %-41s %s" % (e.mbid[:5], e.name[:80], e.artist.name[:60]))
            else:
                print("  %s %-41s" % (e.mbid[:5], e.name[:80] if e.name else ""))

    print()


class DumpElement(Element):
    """
        Accept whatever and print it out in a reasonably sane manner.
    """

    def __init__(self):
        pass

    def inputs(self):
        return []

    def push(self, inputs):

        for input in inputs:
            print_entity_list(input)
