from troi import EntityEnum

def print_entities(entities, count=0):

    if count == 0:
        count = len(entities)

    if entities[0].type == EntityEnum("artist"):
        for e in entities[:count]:
            print("  %s %s" % (str(e.id)[:5], e.name))

    elif entities[0].type == EntityEnum("artist-credit"):
        for e in entities[:count]:
            print("  %7d %s" % (int(e.id), e.mb_artist['artist_name']))

    elif entities[0].type == EntityEnum("recording"):
        for e in entities[:count]:
            print("  %s %-41s %s" % (str(e.id)[:5], e.name[:40], e.mb_artist['artist_credit_name'][:40]))

    print()
