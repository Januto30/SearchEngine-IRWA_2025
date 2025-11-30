import os
import re
import json
from typing import List, Any

try:
	from groq import Groq
except Exception:
	Groq = None

from dotenv import load_dotenv
load_dotenv()


class RAGEnhancedGenerator:
	"""Improved RAG generator that receives retrieved results (list of ResultItem-like objects or dicts)
	and formats a richer prompt including rank and score. The generator returns a structured dict and
	falls back to a deterministic choice (top-ranked) when the LLM output is missing or invalid.
	"""

	PROMPT_TEMPLATE = """
You are an expert product recommender. Below are products retrieved by a search system for a user's request.

Rules:
- Prefer the highest-ranked product (rank 1) unless another product has clearly better attributes (score, price, rating) shown below.
- Return a JSON object EXACTLY in this format (no extra text):
  {{"best_pid": "<PID>", "why": "<explanation>", "alternative": "<PID or empty>", "notes": "<optional>"}}

Retrieved products (top {top_n}):
{retrieved_results}

User query: "{user_query}"

If none of the retrieved products is a good fit, return JSON with best_pid as an empty string and explain why.
"""

	DEFAULT_ANSWER = {
		"best_pid": "",
		"why": "RAG not available or LLM call failed; using deterministic fallback.",
		"alternative": "",
		"notes": "fallback"
	}

	def _format_results(self, retrieved_results: List[Any], top_N: int = 20) -> str:
		"""Format retrieved results into lines with Rank, PID, Score, Title (and short desc if available)."""
		lines = []
		for i, res in enumerate(retrieved_results[:top_N], start=1):
			# support both dict-like and objects with attributes
			if isinstance(res, dict):
				pid = res.get('pid')
				title = res.get('title', '')
				score = res.get('score', res.get('ranking', ''))
				desc = res.get('description', '')
			else:
				pid = getattr(res, 'pid', None)
				title = getattr(res, 'title', '')
				score = getattr(res, 'ranking', '')
				desc = getattr(res, 'description', '')

			short_desc = ''
			if desc:
				# truncate to first 120 chars
				short_desc = (str(desc).strip().replace('\n', ' ')[:120]).strip()

			lines.append(f"Rank: {i}, PID: {pid}, Score: {score}, Title: {title}{', Desc: ' + short_desc if short_desc else ''}")
		return "\n".join(lines)

	def _deterministic_fallback(self, user_query: str, retrieved_results: List[Any]) -> dict:
		"""Pick the top-ranked item deterministically and craft a simple explanation."""
		if not retrieved_results:
			return self.DEFAULT_ANSWER
		top = retrieved_results[0]
		pid = top.get('pid') if isinstance(top, dict) else getattr(top, 'pid', None)
		title = top.get('title') if isinstance(top, dict) else getattr(top, 'title', '')
		why = f"Selected top-ranked product (rank 1) because it best matches the query '{user_query}' based on retrieval score and title match: {title}."
		return {"best_pid": pid or "", "why": why, "alternative": "", "notes": "deterministic_fallback"}

	def _extract_json_from_text(self, text: str) -> dict:
		"""Try to extract a JSON object from the model output. If fail, return {}."""
		if not text:
			return {}
		# try to find a JSON substring
		# common case: model returns plain JSON or text with JSON inside
		try:
			# if the whole text is JSON
			return json.loads(text)
		except Exception:
			# try to locate first {...} block
			m = re.search(r"\{[\s\S]*\}", text)
			if not m:
				return {}
			try:
				return json.loads(m.group(0))
			except Exception:
				return {}

	def generate_response(self, user_query: str, retrieved_results: List[Any], top_N: int = 10, mode: str = 'augment') -> dict:
		"""Generate an enhanced RAG response. Returns a dict with keys: best_pid, why, alternative, notes.

		- `retrieved_results` should be a list of ResultItem-like objects or dicts; items should include `pid` and optionally `ranking`.
		- `mode` can be 'augment' (use LLM) or 'deterministic' (skip LLM and use fallback).
		"""
		# prepare deterministic default
		try:
			formatted = self._format_results(retrieved_results, top_N=top_N)
		except Exception:
			formatted = ""

		prompt = self.PROMPT_TEMPLATE.format(retrieved_results=formatted, user_query=user_query, top_n=top_N)

		# deterministic-only mode
		if mode == 'deterministic' or Groq is None:
			print("RAGEnhanced: deterministic mode or Groq unavailable; using fallback")
			return self._deterministic_fallback(user_query, retrieved_results)

		# call LLM
		try:
			client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
			model_name = os.environ.get('GROQ_MODEL', 'llama-3.1-8b-instant')
			chat_completion = client.chat.completions.create(
				messages=[{"role": "user", "content": prompt}],
				model=model_name,
			)
			generation = chat_completion.choices[0].message.content
		except Exception as e:
			print(f"RAGEnhanced: LLM error: {e}")
			return self._deterministic_fallback(user_query, retrieved_results)

		# try to parse JSON from generation
		parsed = self._extract_json_from_text(generation)
		# if parsed contains best_pid, validate it
		retrieved_pids = set()
		for r in retrieved_results[:top_N]:
			pid = r.get('pid') if isinstance(r, dict) else getattr(r, 'pid', None)
			if pid:
				retrieved_pids.add(str(pid))

		if parsed and parsed.get('best_pid') is not None:
			best_pid = str(parsed.get('best_pid') or "")
			# If LLM returned empty best_pid, respect it
			if best_pid == "":
				return parsed
			if best_pid in retrieved_pids:
				# ok: LLM chose a returned pid
				return parsed
			else:
				# LLM chose something not in retrieved set -> prefer deterministic top
				print(f"RAGEnhanced: LLM chose PID not in retrieved results: {best_pid}; falling back to top-ranked.")
				fallback = self._deterministic_fallback(user_query, retrieved_results)
				fallback['notes'] = 'llm_out_of_scope_fallback'
				fallback['llm_raw'] = generation
				return fallback

		# If parsing failed, attempt to find a line like 'Best Product: <PID>'
		m = re.search(r"Best Product\s*:\s*([A-Za-z0-9_-]+)", generation)
		if m:
			pid_guess = m.group(1)
			if pid_guess in retrieved_pids:
				return {"best_pid": pid_guess, "why": generation, "alternative": "", "notes": "parsed_from_text"}

		# Last resort: deterministic fallback
		print("RAGEnhanced: could not parse LLM output as valid pid -> deterministic fallback")
		fb = self._deterministic_fallback(user_query, retrieved_results)
		fb['llm_raw'] = generation
		return fb


__all__ = ['RAGEnhancedGenerator']
