import copy
import troi

def is_homogeneous(entities):
    '''
        Check to see if all the items in a list of of the same type
    '''

    if not entities:
        return True

    type_set = set()
    for e in entities:
        type_set.add(type(e))

    return len(type_set) == 1


def _ensure_conformity(entities_0, entities_1):
    '''
        Check that both entity lists are homogenous and of the same type.
    '''

    if not is_homogeneous(entities_0):
        raise TypeError("entities_0 list not homogenous")

    if not is_homogeneous(entities_1):
        raise TypeError("entities_1 list not homogenous")

    if entities_0 and entities_1 and type(entities_0[0]) != type(entities_1[0]):
        raise TypeError("entities_0 and entities_1 must both be homogenous with all the same type")

    return True


class UniqueElement(troi.Element):
    '''
        Make this passed list of entities unique base on the passed key
        (must be one of name, mbid or msid) and return the unique list.
        Currently the order of the list is not preserved. This should be improved on...
    '''

    def __init__(self, key = "mbid"):
        self.key = key

    def inputs(self):
        return []

    def read(self, entities_arg):
        entities = entities_arg[0]

        if not entities:
            return []

        if not is_homogeneous(entities):
            raise TypeError("entity list not homogenous")

        if isinstance(entities[0], troi.Artist):
            if self.key not in ['mbids', 'msid', 'name', 'artist_credit_id']:
                raise ValueError("key must be one of mbid/s, msid, name or artist_credit_id.")
        else:
            if self.key not in ['mbid', 'msid', 'name']:
                raise ValueError("key must be one of mbid/s, msid or name.")

        entity_dict = {}
        for e in entities:
            if isinstance(e, troi.Artist) and self.key == "mbids":
                entity_dict[",".join(getattr(e, self.key))] = e
            else:
                entity_dict[getattr(e, self.key)] = e

        return list(entity_dict.values())


class UnionElement(troi.Element):
    '''
        Combine both entities lists into one
    '''

    def __init__(self):
        pass

    def inputs(self):
        return []

    def read(self, entities):
        entities_0 = entities[0]
        entities_1 = entities[1]

        if not entities_0:
            return entities_1

        if not entities_1:
            return entities_0

        _ensure_conformity(entities_0, entities_1)

        result = copy.copy(entities_0)
        result.extend(entities_1)

        return result


class IntersectionElement(troi.Element):
    """
        Return the list of entities that exist in both entities lists.
    """

    def __init__(self, key = "mbid"):
        self.key = key

    def inputs(self):
        return []

    def read(self, entities):
        entities_0 = entities[0]
        entities_1 = entities[1]

        if not entities_0 or not entities_1:
            return []

        _ensure_conformity(entities_0, entities_1)

        if isinstance(entities_0[0], troi.Artist):
            if self.key not in ['mbids', 'msid', 'name', 'artist_credit_id']:
                raise ValueError("key must be one of mbid/s, msid, name or artist_credit_id.")
        else:
            if self.key not in ['mbid', 'msid', 'name']:
                raise ValueError("key must be one of mbid/s, msid or name.")

        entity_dict = {}
        for e in entities_1:
            if isinstance(e, troi.Artist) and self.key == "mbids":
                entity_dict[",".join(getattr(e, self.key))] = e
            else:
                entity_dict[getattr(e, self.key)] = e

        results = []
        for e in entities_0:
            if isinstance(e, troi.Artist) and self.key == "mbids":
                if ",".join(getattr(e, self.key)) in entity_dict:
                    results.append(e)
            else:
                if getattr(e, self.key) in entity_dict:
                    results.append(e)


        return results


class DifferenceElement(troi.Element):
    '''
        Return the list of recordings in entities_0 minus those in entities_1
    '''

    def __init__(self, key = "mbid"):
        self.key = key

    def inputs(self):
        return []

    def read(self, entities):
        entities_0 = entities[0]
        entities_1 = entities[1]

        if not entities_0:
            return []

        if not entities_1:
            return entities_0

        _ensure_conformity(entities_0, entities_1)

        if isinstance(entities_0[0], troi.Artist):
            if self.key not in ['mbids', 'msid', 'name', 'artist_credit_id']:
                raise ValueError("key must be one of mbid/s, msid, name or artist_credit_id.")
        else:
            if self.key not in ['mbid', 'msid', 'name']:
                raise ValueError("key must be one of mbid/s, msid or name.")

        entity_dict = {}
        for e in entities_1:
            if isinstance(e, troi.Artist) and self.key == "mbids":
                entity_dict[",".join(getattr(e, self.key))] = e
            else:
                entity_dict[getattr(e, self.key)] = e

        results = []
        for e in entities_0:
            if isinstance(e, troi.Artist) and self.key == "mbids":
                if ",".join(getattr(e, self.key)) not in entity_dict:
                    results.append(e)
            else:
                if getattr(e, self.key) not in entity_dict:
                    results.append(e)

        return results
