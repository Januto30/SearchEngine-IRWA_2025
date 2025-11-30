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

    # Determine candidate documents using conjunctive (AND) semantics first.
    # Prefer using the BM25/term index if available for faster postings lookup.
    try:
        global _cached_index
    except NameError:
        _cached_index = None

    term_postings = []
    for term in q_terms:
        postings_set = set()
        if '_cached_index' in globals() and _cached_index is not None and term in _cached_index:
            postings_set = set(p[0] for p in _cached_index[term])
        else:
            # fall back to scanning doc_vectors
            for pid, dvec in doc_vectors.items():
                if term in dvec:
                    postings_set.add(pid)

        term_postings.append((term, postings_set))

    # collect only non-empty postings sets
    non_empty_sets = [s for (_, s) in term_postings if s]
    if not non_empty_sets:
        return []

    # If all query terms are present in the corpus, try strict conjunctive (intersection)
    if len(non_empty_sets) == len(q_terms):
        matching_docs = set.intersection(*non_empty_sets)
        if not matching_docs:
            # intersection empty -> fall back to union of all postings
            candidate_docs = set.union(*non_empty_sets)
        else:
            candidate_docs = matching_docs
    else:
        # Some terms missing entirely: use union of available term postings
        candidate_docs = set.union(*non_empty_sets)

    if not candidate_docs:
        return []

    # Score only candidate documents using cosine similarity
    for pid in candidate_docs:
        dvec = doc_vectors.get(pid)
        if not dvec:
            continue
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


def create_bm25_index_from_corpus(corpus: Dict[str, object]):
    """Build inverted index, tf lists, df counts, BM25 idf, and doc lengths/avgdl.

    Returns a tuple (index, tf, df_counts, idf_bm25, doc_len, avgdl, pid_list)
    where `index` maps term -> list of (pid, positions_list)
    """
    from collections import defaultdict
    index = defaultdict(list)
    tf = defaultdict(list)
    df_counts = defaultdict(int)
    doc_texts = {}
    pid_list = []

    # collect text and build postings with positions
    for pid, doc in corpus.items():
        pid_list.append(pid)
        text_parts = []
        if getattr(doc, 'title', None):
            text_parts.append(str(doc.title))
        if getattr(doc, 'description', None):
            text_parts.append(str(doc.description))
        if getattr(doc, 'product_details', None):
            pd = doc.product_details
            if isinstance(pd, dict):
                text_parts.append(' '.join([str(v) for v in pd.values()]))
            elif isinstance(pd, list):
                text_parts.append(' '.join([str(x) for x in pd]))
        text = ' '.join(text_parts)
        doc_texts[pid] = text

    N = max(1, len(doc_texts))

    # build per-doc term postings
    doc_len = {}
    for pid, text in doc_texts.items():
        terms = build_terms(text)
        current_page_index = {}
        for pos, term in enumerate(terms):
            if term in current_page_index:
                current_page_index[term][1].append(pos)
            else:
                # store [pid, positions_list]
                current_page_index[term] = [pid, [pos]]

        # normalization and tf
        norm = math.sqrt(sum(len(posting[1]) ** 2 for posting in current_page_index.values()))
        if norm == 0:
            norm = 1.0

        for term, posting in current_page_index.items():
            freq = len(posting[1])
            tf[term].append(round(freq / norm, 4))
            df_counts[term] += 1
            index[term].append(posting)

        doc_len[pid] = sum(len(p[1]) for p in current_page_index.values())

    # compute BM25-style idf
    idf_bm25 = {}
    for term, df in df_counts.items():
        # Robertson-Sparck Jones idf
        idf_bm25[term] = math.log((N - df + 0.5) / (df + 0.5) + 1e-9)

    avgdl = float(sum(doc_len.values()) / max(1, len(doc_len))) if doc_len else 0.0

    return index, tf, df_counts, idf_bm25, doc_len, avgdl, pid_list


def score_bm25_for_docs(query_terms, index, doc_set, idf_bm25, doc_len, avgdl, k1=1.5, b=0.75):
    from collections import defaultdict
    scores = defaultdict(float)
    if avgdl <= 0:
        avgdl = 1.0

    for term in query_terms:
        if term not in index:
            continue
        postings = index[term]
        idf = idf_bm25.get(term, 0.0)
        for posting in postings:
            doc_id = posting[0]
            if doc_id not in doc_set:
                continue
            freq = len(posting[1])
            dl = doc_len.get(doc_id, 0.0)
            denom = freq + k1 * (1 - b + b * (dl / (avgdl + 1e-9)))
            term_score = idf * ((freq * (k1 + 1.0)) / (denom + 1e-9))
            scores[doc_id] += term_score
    return scores


def bm25_search(query, index, tf, idf_bm25, doc_len, avgdl, pid_map=None, top_k=20):
    query_terms = build_terms(query)
    if not query_terms:
        return []

    # Prefer conjunctive AND semantics, but fall back to union of available term postings
    term_postings = []
    for term in query_terms:
        if term in index:
            term_postings.append(set([posting[0] for posting in index[term]]))
        else:
            # skip missing terms (do not abort immediately)
            continue

    if not term_postings:
        return []

    # If all query terms are present, use intersection; otherwise use union
    if len(term_postings) == len(query_terms):
        matching_docs = set.intersection(*term_postings)
        if not matching_docs:
            # empty intersection -> fall back to union
            matching_docs = set.union(*term_postings)
    else:
        matching_docs = set.union(*term_postings)

    if not matching_docs:
        return []

    raw_scores = score_bm25_for_docs(query_terms, index, matching_docs, idf_bm25, doc_len, avgdl)
    ranked = sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)
    if pid_map:
        return [(pid_map.get(doc_id, doc_id), score) for doc_id, score in ranked[:top_k]]
    return ranked[:top_k]


def score_custom_for_docs(query_terms, index, doc_set, idf_bm25, doc_len, avgdl, corpus):
    # Use BM25 as base then apply feature boosts (rating, price, discount, in_stock)
    raw_bm25 = score_bm25_for_docs(query_terms, index, doc_set, idf_bm25, doc_len, avgdl)
    scores = {}
    # compute some normalization factors
    # try to compute max price and discount from corpus
    max_price = 1.0
    if corpus:
        prices = []
        for pid, d in corpus.items():
            try:
                p = float(getattr(d, 'selling_price', 0) or 0)
                prices.append(p)
            except Exception:
                continue
        if prices:
            max_price = max(1.0, max(prices))

    for doc_id, base in raw_bm25.items():
        boost = 1.0
        try:
            d = corpus.get(doc_id)
            # rating
            rating = float(getattr(d, 'average_rating', 0) or 0)
            rating_norm = min(max(rating / 5.0, 0.0), 1.0)
            # in stock
            out_of_stock = getattr(d, 'out_of_stock', False)
            if isinstance(out_of_stock, str):
                is_out = out_of_stock.strip().lower() in ('true', '1', 'yes')
            else:
                is_out = bool(out_of_stock)
            in_stock_flag = 1.0 if not is_out else 0.0
            # price
            try:
                price = float(getattr(d, 'selling_price', 0) or 0)
            except Exception:
                price = 0.0
            price_norm = price / max_price if max_price > 0 else 0.0
            # discount (try to parse)
            disc_raw = getattr(d, 'discount', 0) or 0
            discount = 0.0
            if isinstance(disc_raw, str):
                m = re.search(r"(\d+)", disc_raw)
                discount = float(m.group(1)) if m else 0.0
            else:
                try:
                    discount = float(disc_raw)
                except Exception:
                    discount = 0.0
            discount_norm = min(max(discount / 100.0, 0.0), 1.0)

            w_rating = 0.35; w_instock = 0.25; w_price = 0.25; w_discount = 0.15
            boost = 1.0 + (w_rating * rating_norm) + (w_instock * in_stock_flag) + (w_price * (1 - price_norm)) + (w_discount * discount_norm)
            boost = max(0.1, min(boost, 3.0))
        except Exception:
            boost = 1.0

        scores[doc_id] = base * boost
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked


__all__ = [
    'build_terms',
    'create_tfidf_index_from_corpus',
    'search_query_tfidf',
]

# Module-level cache to avoid rebuilding the index on every query
_cached_corpus_id = None
_cached_doc_vectors = None
_cached_idf = None
_cached_index = None
_cached_tf = None
_cached_df_counts = None
_cached_idf_bm25 = None
_cached_doc_len = None
_cached_avgdl = None


def search_in_corpus(query: str, corpus: dict, top_k: int = 20, method: str = 'tfidf'):
    """Teacher-facing entrypoint: search the provided corpus for the query.

    This function builds a TF-IDF index for the given corpus on first use
    (or when the corpus object changes) and returns a list of (pid, score)
    ranked by relevance.
    """
    global _cached_corpus_id, _cached_doc_vectors, _cached_idf
    global _cached_index, _cached_tf, _cached_df_counts, _cached_idf_bm25, _cached_doc_len, _cached_avgdl

    # Use the corpus object's id to detect changes
    try:
        cid = id(corpus)
    except Exception:
        cid = None

    if cid != _cached_corpus_id or _cached_doc_vectors is None or _cached_idf is None:
        # rebuild TF-IDF and BM25 indexes
        doc_vectors, idf = create_tfidf_index_from_corpus(corpus)
        index, tf, df_counts, idf_bm25, doc_len, avgdl, pid_list = create_bm25_index_from_corpus(corpus)

        _cached_doc_vectors = doc_vectors
        _cached_idf = idf
        _cached_index = index
        _cached_tf = tf
        _cached_df_counts = df_counts
        _cached_idf_bm25 = idf_bm25
        _cached_doc_len = doc_len
        _cached_avgdl = avgdl
        _cached_corpus_id = cid

    method = (method or 'tfidf').lower()
    if method == 'tfidf':
        return search_query_tfidf(query, _cached_doc_vectors, _cached_idf, top_k=top_k)
    elif method == 'bm25':
        # bm25_search expects pid_map optionally; corpus uses pids as keys already
        ranked = bm25_search(query, _cached_index, _cached_tf, _cached_idf_bm25, _cached_doc_len, _cached_avgdl, pid_map=None, top_k=top_k)
        return ranked
    elif method == 'our' or method == 'custom':
        # compute matching docs using conjunctive AND first
        q_terms = build_terms(query)
        if not q_terms:
            return []
        doc_sets = []
        # collect term postings, but do not abort when a term is missing
        for term in q_terms:
            if term in _cached_index:
                doc_sets.append(set([posting[0] for posting in _cached_index[term]]))
            else:
                # skip missing terms to allow partial matches (union fallback)
                continue
        # if no term postings found at all, return empty
        if not doc_sets:
            return []

        # If all query terms were present, prefer strict conjunctive match,
        # but fall back to union if the intersection is empty. Otherwise use union.
        if len(doc_sets) == len(q_terms):
            matching_docs = set.intersection(*doc_sets)
            if not matching_docs:
                matching_docs = set.union(*doc_sets)
        else:
            matching_docs = set.union(*doc_sets)
        ranked = score_custom_for_docs(q_terms, _cached_index, matching_docs, _cached_idf_bm25, _cached_doc_len, _cached_avgdl, corpus)
        # ranked is list of (doc_id, score)
        return ranked[:top_k]
    else:
        # unknown method -> fallback to tfidf
        return search_query_tfidf(query, _cached_doc_vectors, _cached_idf, top_k=top_k)


__all__.append('search_in_corpus')
