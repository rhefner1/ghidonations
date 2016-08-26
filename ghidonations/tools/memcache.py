import json

from google.appengine.api import memcache
from google.appengine.ext import ndb


# Helper Protobuf entity picklers by Nick Johnson
# http://blog.notdot.net/2009/9/Efficient-model-memcaching
def cache(memcache_key, get_item):
    item_json = memcache.get(memcache_key)

    if not item_json:
        item = get_item()
        memcache.set(memcache_key, json.dumps(item))

    else:
        item = json.loads(item_json)

    return item


def deserialize_entity(data):
    if data is None:
        return None
    else:
        # Getting entity fro protobuf
        return ndb.model_from_protobuf(data)


def flush_memcache():
    return memcache.flush_all()


def gql_cache(memcache_key, get_item):
    cached_query = memcache.get(memcache_key)

    if not cached_query:
        entities = get_item

        serialized = serialize_entities(entities)
        memcache.set(memcache_key, serialized)

    else:
        entities = []
        for e in cached_query:
            entity = deserialize_entity(e)
            entities.append(entity)

    return entities


def gql_count(gql_object):
    try:
        length = len(gql_object)
    except Exception:
        length = gql_object.count()

    return length


def q_cache(q):
    return ndb.get_multi(q.fetch(keys_only=True))


def serialize_entities(models):
    if models is None:
        return None
    else:
        entities_list = []
        for m in models:
            e_proto = serialize_entity(m)
            entities_list.append(e_proto)

        return entities_list


def serialize_entity(model):
    if model is None:
        return None
    else:
        # Encoding entity to protobuf
        return ndb.model_to_protobuf(model)
