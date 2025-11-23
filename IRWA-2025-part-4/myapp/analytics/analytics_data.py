import json
import random
import altair as alt
import pandas as pd


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

    def record_click(self, pid: str, search_id: int = None, user_agent: str = None, remote_addr: str = None, timestamp=None):
        """Record a click event and increment counters. Attempts to enrich with rank/position if available."""
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
