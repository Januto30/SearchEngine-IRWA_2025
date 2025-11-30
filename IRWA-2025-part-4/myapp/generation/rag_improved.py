import os
from dotenv import load_dotenv
load_dotenv()

try:
    from groq import Groq
except Exception:
    Groq = None

import math


class RAGGenerator:
    """Improved RAG generator with simple reranking heuristics, richer prompts
    and a fallback local generator when no external LLM key is available.
    """

    PROMPT_TEMPLATE = (
        "You are an expert product advisor helping users choose the best option from "
        "retrieved e-commerce products.\n\n"
        "Instructions:\n"
        "1) Identify the single best product that matches the user's request.\n"
        "2) Explain why it is the best in plain language, referring to attributes.\n"
        "3) Optionally mention one alternative.\n"
        "4) If none fit, return EXACTLY: There are no good products that fit the request.\n\n"
        "Retrieved products (top {top_n}):\n{retrieved_results}\n\n"
        "User request:\n{user_query}\n\n"
        "Output format:\n- Best Product: [PID] [Title]\n- Why: ...\n- Alternative (optional): ...\n"
    )

    def __init__(self, min_rating_threshold: float = 3.0, use_llm_if_available: bool = True):
        self.min_rating = min_rating_threshold
        self.use_llm = use_llm_if_available and (os.environ.get("GROQ_API_KEY") is not None) and (Groq is not None)

    def _score_document(self, doc) -> float:
        """Compute a lightweight heuristic score for reranking documents.

        We combine normalized average_rating, discount and inverse price.
        Scores are in range ~0..1 (not strictly bounded).
        """
        rating = getattr(doc, "average_rating", None) or 0.0
        discount = getattr(doc, "discount", None) or 0.0
        price = getattr(doc, "selling_price", None)

        # rating contribution [0..1]
        r_score = max(0.0, min(1.0, rating / 5.0))

        # discount contribution [0..1] (cap at 100)
        d_score = max(0.0, min(1.0, discount / 100.0))

        # price contribution: prefer lower prices but avoid division by zero
        if price and price > 0:
            p_score = 1.0 / (1.0 + math.log(price + 1.0))
            # normalize roughly to [0..1] using log scaling
            p_score = max(0.0, min(1.0, p_score))
        else:
            p_score = 0.5

        # weighted sum
        score = 0.6 * r_score + 0.2 * d_score + 0.2 * p_score
        return score

    def _format_product_block(self, doc, score=None) -> str:
        parts = []
        parts.append(f"PID: {getattr(doc, 'pid', '')}")
        parts.append(f"Title: {getattr(doc, 'title', '')}")
        desc = getattr(doc, 'description', None)
        if desc:
            # include a short excerpt
            excerpt = (desc[:250] + '...') if len(desc) > 250 else desc
            parts.append(f"Description: {excerpt}")
        sp = getattr(doc, 'selling_price', None)
        if sp is not None:
            parts.append(f"Price: {sp}")
        disc = getattr(doc, 'discount', None)
        if disc is not None:
            parts.append(f"Discount: {disc}")
        rating = getattr(doc, 'average_rating', None)
        if rating is not None:
            parts.append(f"Rating: {rating}")
        url = getattr(doc, 'url', None)
        if url:
            parts.append(f"URL: {url}")
        if score is not None:
            parts.append(f"Score: {score:.4f}")
        return " | ".join(parts)

    def _local_fallback(self, user_query: str, reranked: list) -> dict:
        """Create a simple local summary if LLM is unavailable.

        It picks the highest-scoring product (if any above threshold) and returns
        a short explanation synthesised from metadata.
        """
        if not reranked:
            return {"answer": "There are no good products that fit the request.", "chosen_pid": None}

        top = reranked[0]
        doc = top["doc"]
        # if rating is too low, declare no good products
        if (getattr(doc, 'average_rating', 0) or 0) < self.min_rating:
            return {"answer": "There are no good products that fit the request.", "chosen_pid": None}

        why = []
        if getattr(doc, 'average_rating', None):
            why.append(f"good rating ({doc.average_rating}/5)")
        if getattr(doc, 'discount', None):
            why.append(f"attractive discount ({doc.discount}%)")
        if getattr(doc, 'selling_price', None):
            why.append(f"price {doc.selling_price}")

        alt = None
        if len(reranked) > 1:
            alt_doc = reranked[1]['doc']
            alt = f"{alt_doc.pid} {alt_doc.title}"

        answer = f"- Best Product: {doc.pid} {doc.title}\n- Why: This product has {' and '.join(why)}."
        if alt:
            answer += f"\n- Alternative: {alt}"

        return {"answer": answer, "chosen_pid": doc.pid, "alternative_pid": alt}

    def generate_response(self, user_query: str, retrieved_results: list, top_N: int = 10) -> dict:
        """Main entrypoint.

        Steps:
        - compute heuristic scores and rerank
        - if no plausible products, return explicit 'no good products' message
        - if LLM key is available, build detailed prompt and call the API
        - otherwise use the local fallback summariser
        Returns a structured dict with fields: `answer`, `chosen_pid`, `alternative_pid`, `reranked_results`.
        """
        # defensive
        if not retrieved_results:
            return {"answer": "There are no good products that fit the request.", "chosen_pid": None, "reranked_results": []}

        # score and rerank
        scored = []
        for doc in retrieved_results:
            s = self._score_document(doc)
            scored.append({"doc": doc, "score": s})
        scored.sort(key=lambda x: x['score'], reverse=True)

        # prepare a serialisable representation for return
        reranked_results = [
            {"pid": item['doc'].pid, "title": item['doc'].title, "score": item['score']}
            for item in scored[:top_N]
        ]

        # quick quality check: if top item rating < threshold -> no good products
        top_doc = scored[0]['doc']
        if (getattr(top_doc, 'average_rating', 0) or 0) < self.min_rating:
            return {"answer": "There are no good products that fit the request.", "chosen_pid": None, "reranked_results": reranked_results}

        # If an LLM is available, use it to generate fluent recommendation
        if self.use_llm:
            try:
                client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
                model_name = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

                formatted = "\n\n".join([
                    self._format_product_block(item['doc'], score=item['score']) for item in scored[:top_N]
                ])

                prompt = self.PROMPT_TEMPLATE.format(
                    retrieved_results=formatted,
                    user_query=user_query,
                    top_n=top_N,
                )

                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model_name,
                )

                generation = chat_completion.choices[0].message.content
                # basic parsing: try to extract chosen PID
                chosen_pid = None
                for line in generation.splitlines():
                    if line.strip().lower().startswith("- best product:"):
                        # attempt to capture PID as first token after colon
                        parts = line.split(":", 1)[1].strip().split()
                        if parts:
                            chosen_pid = parts[0]
                        break

                return {
                    "answer": generation,
                    "chosen_pid": chosen_pid,
                    "reranked_results": reranked_results,
                    "used_model": model_name,
                }
            except Exception as e:
                print(f"RAG LLM call failed: {e}")
                # fall through to local fallback

        # local fallback
        fallback = self._local_fallback(user_query, scored[:top_N])
        fallback["reranked_results"] = reranked_results
        fallback["used_model"] = None
        return fallback
