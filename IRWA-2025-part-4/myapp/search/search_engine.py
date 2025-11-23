import random
import numpy as np

from myapp.search.objects import Document, ResultItem
from myapp.search import algorithms


def dummy_search(corpus: dict, search_id, num_results=20):
    """
    Just a demo method, that returns random <num_results> documents from the corpus
    :param corpus: the documents corpus
    :param search_id: the search id
    :param num_results: number of documents to return
    :return: a list of random documents from the corpus
    """
    res = []
    doc_ids = list(corpus.keys())
    docs_to_return = np.random.choice(doc_ids, size=num_results, replace=False)
    for doc_id in docs_to_return:
        doc = corpus[doc_id]
        res.append(Document(pid=doc.pid, title=doc.title, description=doc.description,
                            url="doc_details?pid={}&search_id={}&param2=2".format(doc.pid, search_id), ranking=random.random()))
    return res


class SearchEngine:
    """Class that implements the search engine logic"""

    def __init__(self):
        # placeholders for TF-IDF index
        self._tfidf_built = False
        self._doc_vectors = None
        self._idf = None

    def search(self, search_query, search_id, corpus, num_results=20, backend: str = 'tfidf'):
        print("Search query:", search_query)

        # keep the original dummy_search available; use TF-IDF by default
        if backend == 'dummy':
            return dummy_search(corpus, search_id, num_results=num_results)

        # use the single teacher-facing entrypoint that builds/caches the TF-IDF index
        if backend == 'tfidf':
            try:
                ranked = algorithms.search_in_corpus(search_query, corpus, top_k=num_results)
            except Exception as e:
                print(f"Error during TF-IDF search via search_in_corpus: {e}")
                return dummy_search(corpus, search_id, num_results=num_results)

            results = []
            for pid, score in ranked:
                if pid not in corpus:
                    continue
                doc = corpus[pid]
                results.append(ResultItem(pid=doc.pid, title=doc.title, description=doc.description,
                                          url=f"doc_details?pid={doc.pid}&search_id={search_id}", ranking=score))
            return results

        # fallback to dummy if backend unknown
        return dummy_search(corpus, search_id, num_results=num_results)
