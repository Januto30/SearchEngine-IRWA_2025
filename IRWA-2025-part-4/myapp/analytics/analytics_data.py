import json
import os
import random
import altair as alt
import pandas as pd
import httpagentparser
from collections import Counter

# geoip2 is optional; we import lazily and handle absence gracefully
_HAS_GEOIP2 = False
try:
    import geoip2.database  # type: ignore
    _HAS_GEOIP2 = True
except Exception:
    _HAS_GEOIP2 = False


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
        # optional GeoIP reader (lazy init) and cache for IP lookups
        self._geo_reader = None
        self._geo_db_path = os.getenv('GEOIP_DB_PATH', 'GeoLite2-City.mmdb')
        self._ip_lookup_cache = {}

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

    # Return counts per remote IP (city required GeoIP integration)
    def get_ip_stats(self):
        counts = Counter()
        for ev in self.click_events:
            ip = ev.get('remote_addr') or 'unknown'
            counts[ip] += 1

        results = []
        for ip, c in counts.most_common():
            info = self._resolve_ip_to_location(ip)
            row = {'ip': ip, 'count': c}
            if info:
                row.update(info)
            results.append(row)
        return results

    def _init_geo_reader(self):
        if not _HAS_GEOIP2:
            return None
        if self._geo_reader:
            return self._geo_reader
        # try to open the database file
        db_path = self._geo_db_path
        try:
            if not os.path.isabs(db_path):
                # check common locations relative to project root
                candidates = [db_path, os.path.join('/usr/local/share/GeoIP', db_path), os.path.join('/usr/share/GeoIP', db_path)]
            else:
                candidates = [db_path]
            for p in candidates:
                if os.path.exists(p):
                    self._geo_reader = geoip2.database.Reader(p)
                    return self._geo_reader
        except Exception:
            self._geo_reader = None
        return None

    def _resolve_ip_to_location(self, ip: str):
        # Return dict with city/country/latitude/longitude if possible, else None
        if not ip or ip == 'unknown':
            return None
        if ip in self._ip_lookup_cache:
            return self._ip_lookup_cache[ip]
        reader = self._init_geo_reader()
        if not reader:
            # no geoip available
            self._ip_lookup_cache[ip] = None
            return None
        try:
            resp = reader.city(ip)
            city = resp.city.name if resp.city and resp.city.name else None
            country = resp.country.name if resp.country and resp.country.name else None
            subdivision = None
            if resp.subdivisions and len(resp.subdivisions) > 0:
                subdivision = resp.subdivisions[0].name
            lat = resp.location.latitude if resp.location else None
            lon = resp.location.longitude if resp.location else None
            info = {}
            if city:
                info['city'] = city
            if subdivision:
                info['region'] = subdivision
            if country:
                info['country'] = country
            if lat is not None and lon is not None:
                info['latitude'] = lat
                info['longitude'] = lon
            # cache even if empty dict to avoid repeated lookups
            self._ip_lookup_cache[ip] = info or None
            return self._ip_lookup_cache[ip]
        except Exception:
            self._ip_lookup_cache[ip] = None
            return None

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
