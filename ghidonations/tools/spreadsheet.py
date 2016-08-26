import logging

import appengine_config
import cloudstorage as gcs
import pipeline
from google.appengine.api import memcache, search


def check_task_completion(s, job_id):
    m = memcache.get(job_id)
    if m == None or m == 0:
        return False, None
    else:
        return True, m


def get_all_search_docs(index_name):
    index = search.Index(name=index_name)

    documents = []
    last_doc_id = None
    completed = False

    while not completed:
        docs_query = index.get_range(start_id=last_doc_id, limit=1000, include_start_object=False)

        if docs_query.results:
            documents.extend(docs_query.results)
            last_doc_id = docs_query.results[-1].doc_id

        else:
            completed = True

    return documents


def new_file(mime_type, file_name):
    gcs_file_key = appengine_config.GCS_BUCKET + "/" + file_name

    write_retry_params = gcs.RetryParams(backoff_factor=1.1)
    gcs_file = gcs.open(gcs_file_key, 'w', content_type=mime_type,
                        retry_params=write_retry_params)

    return gcs_file_key, gcs_file


def pipeline_status(job_id):
    pipeline_id = memcache.get("id" + job_id)

    if pipeline_id:
        status_tree = pipeline.get_status_tree(pipeline_id)

        total_pipelines = 0
        pipelines_finished = 0

        for pipe in status_tree["pipelines"].values():

            status = pipe['status']
            logging.info(status)

            if status == "aborted":
                logging.error("Error in pipelineStatus with job_id: " + job_id)

            if status == "filled" or status == "done":
                pipelines_finished += 1

            total_pipelines += 1

        percentage = float(pipelines_finished) / float(total_pipelines)
        return int(percentage * 100)

    else:
        logging.debug("Could not find pipeline_id, defaulting to status=0")
        return 0
