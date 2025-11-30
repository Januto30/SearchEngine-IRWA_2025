import os
from json import JSONEncoder

import httpagentparser  # for getting the user agent as json
from flask import Flask, render_template, session
from flask import request, jsonify

from myapp.analytics.analytics_data import AnalyticsData, ClickedDoc
from myapp.search.load_corpus import load_corpus
from myapp.search.objects import Document, StatsDocument
from myapp.search.search_engine import SearchEngine
from myapp.generation.rag import RAGGenerator

from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env


# *** for using method to_json in objects ***
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)
_default.default = JSONEncoder().default
JSONEncoder.default = _default
# end lines ***for using method to_json in objects ***


# instantiate the Flask application
app = Flask(__name__)

# random 'secret_key' is used for persisting data in secure cookie
app.secret_key = os.getenv("SECRET_KEY")
# open browser dev tool to see the cookies
app.session_cookie_name = os.getenv("SESSION_COOKIE_NAME")
# instantiate our search engine
search_engine = SearchEngine()
# instantiate our in memory persistence
analytics_data = AnalyticsData()
# instantiate the baseline RAG generator (keep `rag.py` unchanged)
rag_generator = RAGGenerator()

# load documents corpus into memory.
full_path = os.path.realpath(__file__)
path, filename = os.path.split(full_path)
file_path = path + "/" + os.getenv("DATA_FILE_PATH")
corpus = load_corpus(file_path)
# Log first element of corpus to verify it loaded correctly:
print("\nCorpus is loaded... \n First element:\n", list(corpus.values())[0])


# Home URL "/"
@app.route('/')
def index():
    print("starting home url /...")

    # flask server creates a session by persisting a cookie in the user's browser.
    # the 'session' object keeps data between multiple requests. Example:
    session['some_var'] = "Some value that is kept in session"

    user_agent = request.headers.get('User-Agent')
    print("Raw user browser:", user_agent)

    user_ip = request.remote_addr
    agent = httpagentparser.detect(user_agent)

    print("Remote IP: {} - JSON user browser {}".format(user_ip, agent))
    print(session)
    return render_template('index.html', page_title="Welcome")


@app.route('/search', methods=['POST'])
def search_form_post():
    
    search_query = request.form['search-query']

    session['last_search_query'] = search_query

    search_id = analytics_data.save_query_terms(search_query)

    # determine ranking method from user session (default: tfidf)
    ranking_method = session.get('ranking_method', 'tfidf')
    results = search_engine.search(search_query, search_id, corpus, num_results=20, backend=ranking_method)

    # Save results for analytics attribution (so clicks can be mapped to search_id/position)
    try:
        analytics_data.save_search_results(search_id, results)
    except Exception as e:
        print(f"Warning: could not save search results for analytics: {e}")

    # generate RAG response based on user query and retrieved results
    # Use the baseline RAG implementation from `rag.py`
    try:
        rag_response = rag_generator.generate_response(search_query, results)
    except Exception as e:
        print(f"RAG generation error: {e}")
        rag_response = "RAG is not available. Check your credentials (.env file) or account limits."
    print("RAG response:", rag_response)

    # Support both legacy string response and new structured dict response
    if isinstance(rag_response, dict):
        rag_text = rag_response.get('answer')
        rag_reranked = rag_response.get('reranked_results')
    else:
        rag_text = rag_response
        rag_reranked = None

    found_count = len(results)
    session['last_found_count'] = found_count

    print(session)

    return render_template(
        'results.html',
        results_list=results,
        page_title="Results",
        found_counter=found_count,
        rag_response=rag_response,
        rag_text=rag_text,
        rag_reranked=rag_reranked,
        corpus=corpus,
    )


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Simple settings page to select the ranking algorithm (stored in session)."""
    if request.method == 'POST':
        method = request.form.get('ranking_method', 'tfidf')
        session['ranking_method'] = method
    current = session.get('ranking_method', 'tfidf')
    return render_template('settings.html', current_method=current)


@app.route('/doc_details', methods=['GET'])
def doc_details():
    """
    Show document details page
    ### Replace with your custom logic ###
    """

    # getting request parameters:
    # user = request.args.get('user')
    print("doc details session: ")
    print(session)

    res = session["some_var"]
    print("recovered var from session:", res)

    # get the query string parameters from request
    clicked_doc_id = request.args.get("pid")
    print("click in id={}".format(clicked_doc_id))

    # optional search id for attribution
    try:
        search_id = int(request.args.get('search_id')) if request.args.get('search_id') else None
    except Exception:
        search_id = None

    # record click with analytics helper (this also increments fact_clicks)
    analytics_data.record_click(pid=clicked_doc_id,
                                search_id=search_id,
                                user_agent=request.headers.get('User-Agent'),
                                remote_addr=request.remote_addr)

    print("fact_clicks count for id={} is {}".format(clicked_doc_id, analytics_data.fact_clicks.get(clicked_doc_id)))

    # find document in corpus and render details
    doc = corpus.get(clicked_doc_id)
    return render_template('doc_details.html', doc=doc)


@app.route('/stats', methods=['GET'])
def stats():
    """
    Show simple statistics example. ### Replace with yourdashboard ###
    :return:
    """

    docs = []
    for doc_id in analytics_data.fact_clicks:
        row: Document = corpus[doc_id]
        count = analytics_data.fact_clicks[doc_id]
        doc = StatsDocument(pid=row.pid, title=row.title, description=row.description, url=row.url, count=count)
        docs.append(doc)
    
    # simulate sort by ranking
    docs.sort(key=lambda doc: doc.count, reverse=True)
    return render_template('stats.html', clicks_data=docs)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    visited_docs = []
    for doc_id in analytics_data.fact_clicks.keys():
        d: Document = corpus[doc_id]
        doc = ClickedDoc(doc_id, d.description, analytics_data.fact_clicks[doc_id])
        visited_docs.append(doc)

    # simulate sort by ranking
    visited_docs.sort(key=lambda doc: doc.counter, reverse=True)

    for doc in visited_docs: print(doc)
    return render_template('dashboard.html', visited_docs=visited_docs)


# New route added for generating an examples of basic Altair plot (used for dashboard)
@app.route('/plot_number_of_views', methods=['GET'])
def plot_number_of_views():
    return analytics_data.plot_number_of_views()


### Analytics JSON endpoints used by the dashboard UI ###
@app.route('/analytics/top_clicked', methods=['GET'])
def analytics_top_clicked():
    data = analytics_data.get_top_clicked(n=50)
    return jsonify({'top_clicked': data})


@app.route('/analytics/browsers', methods=['GET'])
def analytics_browsers():
    data = analytics_data.get_browser_stats()
    return jsonify({'browsers': data})


@app.route('/analytics/top_queries', methods=['GET'])
def analytics_top_queries():
    data = analytics_data.get_top_queries(n=50)
    return jsonify({'top_queries': data})


@app.route('/analytics/top_terms', methods=['GET'])
def analytics_top_terms():
    data = analytics_data.get_top_terms(n=50)
    return jsonify({'top_terms': data})


@app.route('/analytics/ips', methods=['GET'])
def analytics_ips():
    data = analytics_data.get_ip_stats()
    return jsonify({'ips': data})


if __name__ == "__main__":
    app.run(port=8088, host="0.0.0.0", threaded=False, debug=os.getenv("DEBUG"))