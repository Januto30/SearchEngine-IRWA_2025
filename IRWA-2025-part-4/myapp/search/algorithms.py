import re
import math
from typing import Dict, List, Tuple


def build_terms(text: str) -> List[str]:
    """Simple tokenizer: lowercase, remove non-alphanumeric, split on whitespace."""
    if not text:
        return []
    text = text.lower()
    # replace non-alphanumeric characters with spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    terms = [t for t in text.split() if len(t) > 1]
    return terms


def create_tfidf_index_from_corpus(corpus: Dict[str, object]) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float]]:
    """
    Build a simple TF-IDF vector representation for each document in the corpus.

    Returns:
      - doc_vectors: mapping pid -> {term: tf-idf}
      - idf: mapping term -> idf
    """
    # collect term frequencies per document
    term_doc_freq = {}  # term -> set of pids
    doc_term_freqs = {}  # pid -> term -> raw count

    for pid, doc in corpus.items():
        text_parts = []
        if getattr(doc, 'title', None):
            text_parts.append(str(doc.title))
        if getattr(doc, 'description', None):
            text_parts.append(str(doc.description))
        if getattr(doc, 'product_details', None):
            # if product_details is dict, join values
            pd = doc.product_details
            if isinstance(pd, dict):
                text_parts.append(' '.join([str(v) for v in pd.values()]))
            elif isinstance(pd, list):
                text_parts.append(' '.join([str(x) for x in pd]))

        text = ' '.join(text_parts)
        terms = build_terms(text)
        freqs = {}
        for t in terms:
            freqs[t] = freqs.get(t, 0) + 1
        doc_term_freqs[pid] = freqs
        for t in freqs.keys():
            s = term_doc_freq.get(t)
            if s is None:
                term_doc_freq[t] = {pid}
            else:
                s.add(pid)

    N = max(1, len(corpus))
    idf = {}
    for term, docset in term_doc_freq.items():
        df = len(docset)
        idf[term] = math.log((1 + N) / (1 + df))

    # build TF-IDF vectors (using raw freq normalized by L2)
    doc_vectors = {}
    for pid, freqs in doc_term_freqs.items():
        # compute L2 norm of tf values
        norm = math.sqrt(sum((v ** 2) for v in freqs.values()))
        if norm == 0:
            norm = 1.0
        vec = {}
        for term, cnt in freqs.items():
            tf = cnt / norm
            vec[term] = tf * idf.get(term, 0.0)
        doc_vectors[pid] = vec

    return doc_vectors, idf


def search_query_tfidf(query: str, doc_vectors: Dict[str, Dict[str, float]], idf: Dict[str, float], top_k: int = 20) -> List[Tuple[str, float]]:
    """Search using cosine similarity between query TF-IDF and document vectors.

    Returns a list of tuples (pid, score) sorted by score desc.
    """
    q_terms = build_terms(query)
    if not q_terms:
        return []

    # compute raw term counts for query
    q_freqs = {}
    for t in q_terms:
        q_freqs[t] = q_freqs.get(t, 0) + 1

    # compute query tf-idf vector
    q_norm = math.sqrt(sum((v ** 2) for v in q_freqs.values()))
    if q_norm == 0:
        q_norm = 1.0
    q_vec = {}
    for term, cnt in q_freqs.items():
        tf = cnt / q_norm
        q_vec[term] = tf * idf.get(term, 0.0)

    # compute similarity with documents
    results = []
    # precompute query norm
    q_vec_norm = math.sqrt(sum(v * v for v in q_vec.values()))
    if q_vec_norm == 0:
        return []

    for pid, dvec in doc_vectors.items():
        # dot product
        dot = 0.0
        for term, qv in q_vec.items():
            dv = dvec.get(term)
            if dv is not None:
                dot += qv * dv
        if dot == 0.0:
            continue
        dnorm = math.sqrt(sum(v * v for v in dvec.values()))
        if dnorm == 0.0:
            continue
        score = dot / (q_vec_norm * dnorm)
        results.append((pid, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


__all__ = [
    'build_terms',
    'create_tfidf_index_from_corpus',
    'search_query_tfidf',
]

# Module-level cache to avoid rebuilding the index on every query
_cached_corpus_id = None
_cached_doc_vectors = None
_cached_idf = None


def search_in_corpus(query: str, corpus: dict, top_k: int = 20):
    """Teacher-facing entrypoint: search the provided corpus for the query.

    This function builds a TF-IDF index for the given corpus on first use
    (or when the corpus object changes) and returns a list of (pid, score)
    ranked by relevance.
    """
    global _cached_corpus_id, _cached_doc_vectors, _cached_idf

    # Use the corpus object's id to detect changes
    try:
        cid = id(corpus)
    except Exception:
        cid = None

    if cid != _cached_corpus_id or _cached_doc_vectors is None or _cached_idf is None:
        # rebuild index
        doc_vectors, idf = create_tfidf_index_from_corpus(corpus)
        _cached_doc_vectors = doc_vectors
        _cached_idf = idf
        _cached_corpus_id = cid

    # run the tfidf search
    results = search_query_tfidf(query, _cached_doc_vectors, _cached_idf, top_k=top_k)
    return results


__all__.append('search_in_corpus')
