import json
import random
import altair as alt
import pandas as pd
import httpagentparser
from collections import Counter


class AnalyticsData:
    """An in-memory analytics store used for the educational demo.

    Stores:
    - queries: mapping search_id -> {terms, timestamp, num_terms}
    - search_results: mapping search_id -> list of {pid, rank, position}
    - fact_clicks: mapping pid -> count
    - click_events: list of detailed click records
    """

    def __init__(self):
        self._next_search_id = 1
        self.queries = {}
        self.search_results = {}
        self.fact_clicks = {}
        self.click_events = []

    def save_query_terms(self, terms: str) -> int:
        """Save the query and return a search_id."""
        sid = self._next_search_id
        self._next_search_id += 1
        self.queries[sid] = {
            "terms": terms,
            "timestamp": pd.Timestamp.utcnow(),
            "num_terms": len(terms.split()) if terms else 0,
        }
        return sid

    def save_search_results(self, search_id: int, results: list):
        """Store results for a search so clicks can be associated later.

        `results` is expected to be an iterable of objects with `.pid` and optionally
        `.ranking` attributes.
        """
        rows = []
        for pos, item in enumerate(results, start=1):
            pid = getattr(item, 'pid', None)
            rank = getattr(item, 'ranking', None)
            rows.append({"pid": pid, "rank": rank, "position": pos})
        self.search_results[search_id] = rows
    
    def plot_number_of_views(self):
        # Prepare data
        data = [{'Document ID': doc_id, 'Number of Views': count} for doc_id, count in self.fact_clicks.items()]
        df = pd.DataFrame(data)
        # Create Altair chart
        chart = alt.Chart(df).mark_bar().encode(
            x='Document ID',
            y='Number of Views'
        ).properties(
            title='Number of Views per Document'
        )
        # Render the chart to HTML
        return chart.to_html()

    # Return top queries by frequency
    def get_top_queries(self, n=10):
        counts = Counter()
        for sid, v in self.queries.items():
            terms = v.get('terms')
            if terms:
                counts[terms] += 1
        return [{'query': q, 'count': c} for q, c in counts.most_common(n)]

    # Return top individual terms across saved queries
    def get_top_terms(self, n=20):
        counts = Counter()
        for sid, v in self.queries.items():
            terms = v.get('terms')
            if not terms:
                continue
            toks = [t for t in terms.lower().split() if len(t) > 1]
            counts.update(toks)
        return [{'term': t, 'count': c} for t, c in counts.most_common(n)]

    # Return counts per browser parsed from click_events user_agent
    def get_browser_stats(self):
        counts = Counter()
        for ev in self.click_events:
            ua = ev.get('user_agent')
            if not ua:
                counts['unknown'] += 1
                continue
            try:
                info = httpagentparser.detect(ua)
                browser = info.get('browser', {}).get('name') or info.get('browser') or 'unknown'
            except Exception:
                browser = 'unknown'
            counts[browser] += 1
        return [{'browser': b, 'count': c} for b, c in counts.most_common()]

    # Return counts per remote IP (city requires GeoIP integration)
    def get_ip_stats(self):
        counts = Counter()
        for ev in self.click_events:
            ip = ev.get('remote_addr') or 'unknown'
            counts[ip] += 1
        return [{'ip': ip, 'count': c} for ip, c in counts.most_common()]

    # Record a click event and increment counters. Attempts to enrich with rank/position if available
    def record_click(self, pid: str, search_id: int = None, user_agent: str = None, remote_addr: str = None, timestamp=None):
        if timestamp is None:
            timestamp = pd.Timestamp.utcnow()

        position = None
        rank = None
        if search_id and search_id in self.search_results:
            for row in self.search_results[search_id]:
                if row.get('pid') == pid:
                    position = row.get('position')
                    rank = row.get('rank')
                    break

        # increment total clicks counter
        self.fact_clicks[pid] = self.fact_clicks.get(pid, 0) + 1

        # append a detailed click event
        self.click_events.append({
            'pid': pid,
            'search_id': search_id,
            'position': position,
            'rank': rank,
            'user_agent': user_agent,
            'remote_addr': remote_addr,
            'timestamp': timestamp,
        })

    def get_top_clicked(self, n=10):
        rows = [{'pid': pid, 'count': count} for pid, count in self.fact_clicks.items()]
        df = pd.DataFrame(rows)
        if df.empty:
            return []
        df = df.sort_values('count', ascending=False).head(n)
        return df.to_dict(orient='records')


class ClickedDoc:
    def __init__(self, doc_id, description, counter):
        self.doc_id = doc_id
        self.description = description
        self.counter = counter

    def to_json(self):
        return self.__dict__

    def __str__(self):
        """
        Print the object content as a JSON string
        """
        return json.dumps(self)
