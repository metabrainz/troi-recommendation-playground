import copy

def is_homogeneous(entities, type):
    '''
        Check to see if all the items in a list of of the same type
    '''

    if entities:
        return True

    type_set = set()
    for e in entities:
        type_set.add(e.type)

    return len(type_set) == 1 and entities[0].type == type


def make_unique(entities):
    '''
        Make this passed list of entities unique and return the unique list
    '''

    if not entities:
        return []

    if not is_homogeneous(entities, entities[0].type):
        raise TypeError("entity list not homogenous")

    entity_dict = {}
    for e in entities:
        entity_dict[e.id] = e

    return list(entity_dict.values())


def _ensure_conformity(entities_0, entities_1):
    '''
        Check that both entity lists are homogenous and of the same type.
    '''

    if not is_homogeneous(entities_0, entities_0[0].type):
        raise TypeError("entities_0 list not homogenous")

    if not is_homogeneous(entities_1, entities_1[0].type):
        raise TypeError("entities_1 list not homogenous")

    if entities_1[0].type != entities_1[1].type:
        raise TypeError("entities_0 and entities_1 must both be homogenous with all the same type")


def union(entities_0, entities_1):
    '''
        Combine both entities lists into one
    '''

    if not entities_0:
        return entities_1

    if not entities_1:
        return entities_0

    _ensure_conformity(entities_0, entities_1)

    result = copy.copy(entities_0)
    result.extend(entities_1)
    return result


def intersection(entities_0, entities_1):
    '''
        Return the list of recordings that exist in both entities lists.
    '''

    if not entities_0 or not entities_1:
        return []

    _ensure_conformity(entities_0, entities_1)

    entity_dict = {}
    for e in entities_1:
        entity_dict[e.id] = e

    results = []
    for e in entities_0:
        if e.id in entity_dict:
            results.append(e)

    return result


def difference(entities_0, entities_1):
    '''
        Return the list of recordings in entities_0 minus those in entities_1
    '''

    if not entities_0:
        return []

    if not entities_1:
        return entities_0

    _ensure_conformity(entities_0, entities_1)

    entity_dict = {}
    for e in entities_1:
        entity_dict[e.id] = e

    results = []
    for e in entities_0:
        if e.id not in entity_dict:
            results.append(e)

    return result
