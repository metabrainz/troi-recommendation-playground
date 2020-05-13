

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

    if not is_homogeneous(entities, entities[0].type):
        raise TypeError("entity list not homogenous")

    entity_dict = {}
    for e in entities:
        entity_dict[e.id] = e

    return list(entity_dict.values())
