from ghidonations.tools.util import get_key
from google.appengine.api import taskqueue
from google.appengine.ext import deferred


def search_return_all(query, search_results, settings, search_function, entity_return=True):
    all_results = []
    results = search_results

    end_of_results = False

    while end_of_results is False:
        if entity_return is True:
            all_results += search_to_entities(results)

        else:
            all_results.extend(search_to_documents(results))

        query_cursor = results.cursor
        if not query_cursor:
            # Stop the loop
            end_of_results = True

        else:
            # Otherwise, fetch the next results
            results = search_function(query, query_cursor=query_cursor, entity_return=entity_return)[0]

    return all_results


def search_to_documents(search_results):
    documents = []

    for r in search_results:
        documents.append(r)

    return documents


def search_to_entities(search_results):
    entities = []

    for r in search_results:
        key = r.fields[0].value
        d = get_key(key).get()
        entities.append(d)

    return entities


def index_entities_from_query(query, query_cursor=None):
    entities, new_cursor, more = query.fetch_page(20, start_cursor=query_cursor, keys_only=True)

    # If there are more results, kick off concurrent request to get things done faster
    if new_cursor:
        deferred.defer(index_entities_from_query, query, query_cursor=new_cursor, _queue="backend")

    for e in entities:
        taskqueue.add(url="/tasks/delayindexing", params={'e': e.urlsafe()}, queue_name="delayindexing")