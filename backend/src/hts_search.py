"""
HTS search and classification logic.

Flow per user message:
    1. Embed the query (OpenAI)
    2. Search Pinecone (top 5)
    3a. Score >= HIGH_CONFIDENCE  →  return results. Zero Claude calls.
    3b. Score < HIGH_CONFIDENCE   →  one Claude call: either pick a result
                                      or generate a clarifying question.
    3c. Clarification limit hit   →  return top results, let user pick.

Session state (conversation history + clarification count) lives in app.py.
"""

import os
import json
import re
import logging
import hashlib
import time
import pandas as pd
from openai import OpenAI
from pinecone import Pinecone, SearchQuery, SearchRerank
from anthropic import Anthropic

logger = logging.getLogger(__name__)

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "hts-codes-v2")
EMBEDDING_MODEL = "text-embedding-3-large"  # index was built with 3072-dim large
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
CLAUDE_MODEL_LIGHT = os.getenv("CLAUDE_MODEL_LIGHT", "claude-haiku-4-5-20251001")

# Reranking: fetch more candidates, then rerank to top_k
RERANK_FETCH_K = 30     # How many to fetch from vector search
RERANK_MODEL = "pinecone-rerank-v0"

# Cache settings
CACHE_TTL = 3600        # 1 hour
CACHE_MAX_SIZE = 10000

HIGH_CONFIDENCE = 0.65   # Return directly, no Claude call (interactive chat)
BATCH_CONFIDENCE = 0.55  # More aggressive threshold for batch mode (skip Claude above this)
MAX_CLARIFICATIONS = 3   # Back-and-forth limit before presenting top results


class TTLCache:
    """Simple dict-based cache with TTL and max size."""

    def __init__(self, ttl=CACHE_TTL, max_size=CACHE_MAX_SIZE):
        self._store = {}
        self._ttl = ttl
        self._max_size = max_size

    def get(self, key):
        entry = self._store.get(key)
        if entry and time.time() - entry["ts"] < self._ttl:
            return entry["val"]
        if entry:
            del self._store[key]
        return None

    def set(self, key, val):
        if len(self._store) >= self._max_size:
            # Evict oldest 10%
            sorted_keys = sorted(self._store, key=lambda k: self._store[k]["ts"])
            for k in sorted_keys[: self._max_size // 10]:
                del self._store[k]
        self._store[key] = {"val": val, "ts": time.time()}


class HTSSearch:
    def __init__(self):
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = pc.Index(INDEX_NAME)
        self.hts_lookup = self._load_csv()
        self._embed_cache = TTLCache()
        self._search_cache = TTLCache()
        logger.info(f"HTSSearch ready — {len(self.hts_lookup)} leaf nodes loaded from CSV")

    # ── CSV lookup (loaded once at startup) ──────────────────────────

    def _load_csv(self):
        """
        Load every leaf-node HTS entry into a dict keyed by HTS number.
        This is the source of truth for duty rates; Pinecone metadata is
        a secondary copy that may lag behind a CSV update.
        """
        csv_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "hts_2026_revision_4_enriched.csv"
        )
        df = pd.read_csv(csv_path, low_memory=False)
        df = df[df["Is Leaf Node"].astype(str).str.strip() == "Yes"].copy()

        # Normalise NaN → empty string for all text columns we use
        for col in ("Enhanced Description", "General Rate of Duty",
                    "Special Rate of Duty", "Unit of Quantity", "Context Path"):
            df[col] = df[col].fillna("")

        lookup = {}
        for _, row in df.iterrows():
            code = str(row["HTS Number"]).strip()
            if code:
                lookup[code] = {
                    "description": str(row["Enhanced Description"]),
                    "general_rate": str(row["General Rate of Duty"]),
                    "special_rate": str(row["Special Rate of Duty"]),
                    "unit": self._clean_unit(str(row["Unit of Quantity"])),
                    "context_path": str(row["Context Path"]),
                }
        return lookup

    @staticmethod
    def _clean_unit(val):
        """Strip list-like wrapping from unit strings stored as '["kg"]'."""
        val = val.strip()
        if val.startswith('["') and val.endswith('"]'):
            return val[2:-2]
        if val.startswith("[") and val.endswith("]"):
            return val[1:-1].strip("\"'")
        return val

    # ── Embedding & Pinecone search ───────────────────────────────────

    @staticmethod
    def _cache_key(text):
        return hashlib.sha256(text.encode()).hexdigest()

    def _embed(self, text):
        key = self._cache_key(text)
        cached = self._embed_cache.get(key)
        if cached is not None:
            return cached
        resp = self.openai.embeddings.create(input=[text], model=EMBEDDING_MODEL)
        embedding = resp.data[0].embedding
        self._embed_cache.set(key, embedding)
        return embedding

    def _search_pinecone(self, embedding, query_text="", top_k=10):
        """
        Search Pinecone with reranking.

        Uses the search() API: fetches RERANK_FETCH_K candidates by vector
        similarity, then reranks them using the built-in reranker to get
        the best top_k results.

        Falls back to legacy query() API if search() fails.
        """
        try:
            resp = self.index.search(
                namespace="__default__",
                query=SearchQuery(
                    top_k=RERANK_FETCH_K,
                    vector={"values": embedding},
                ),
                rerank=SearchRerank(
                    model=RERANK_MODEL,
                    rank_fields=["description"],
                    top_n=top_k,
                    query=query_text,
                ),
            )
            return ("search", resp)
        except Exception as e:
            logger.warning(f"search() API failed, falling back to query(): {e}")
            return ("query", self.index.query(
                vector=embedding, top_k=top_k, include_metadata=True
            ))

    # ── Result formatting ─────────────────────────────────────────────

    @staticmethod
    def _format_hts_code(code):
        """Normalize any code string to XXXX.XX.XXXX."""
        digits = "".join(c for c in str(code) if c.isdigit())
        if len(digits) >= 10:
            return f"{digits[:4]}.{digits[4:6]}.{digits[6:10]}"
        return str(code)

    def _extract_matches(self, pinecone_resp):
        """
        Normalize search() and query() responses into a common list of
        (score, metadata_dict) tuples.
        """
        api_type, resp = pinecone_resp

        if api_type == "query":
            return [
                (m.score, m.metadata or {})
                for m in (resp.matches if resp.matches else [])
            ]

        # search() API: resp.result.hits
        hits = resp.result.hits if resp.result and resp.result.hits else []
        matches = []
        for hit in hits:
            score = hit._score if hasattr(hit, "_score") else 0.0
            fields = hit.fields if hasattr(hit, "fields") else {}
            matches.append((score, fields or {}))
        return matches

    def _format_result(self, score, meta):
        """
        Turn a (score, metadata) pair into the dict the frontend renders.
        CSV is authoritative for duty rates; Pinecone metadata is fallback.
        """
        raw_code = meta.get("hts_code", "")
        csv = self.hts_lookup.get(raw_code, {})

        return {
            "hts_code": self._format_hts_code(raw_code),
            "description": csv.get("description") or meta.get("description", ""),
            "effective_duty": csv.get("general_rate") or meta.get("general_rate", ""),
            "special_duty": csv.get("special_rate") or meta.get("special_rate", ""),
            "unit": csv.get("unit") or meta.get("unit", ""),
            "confidence_score": round(score * 100),
            "chapter": self._format_hts_code(raw_code)[:2],
            "match_type": "vector_search",
            "duty_source": "usitc",
        }

    # ── CSV reload ──────────────────────────────────────────────────────

    def reload_csv(self):
        """Re-read the CSV from disk (after an update) and refresh the lookup."""
        self.hts_lookup = self._load_csv()
        logger.info(f"CSV reloaded — {len(self.hts_lookup)} leaf nodes")

    # ── Batch-optimised methods (search-first, then one Claude call) ──

    def search_only(self, description):
        """
        Embed + Pinecone search only. No Claude call.
        Returns { results: [...], top_score: float }
        """
        # Check search cache
        cache_key = self._cache_key(description)
        cached = self._search_cache.get(cache_key)
        if cached is not None:
            return cached

        embedding = self._embed(description)
        pinecone_resp = self._search_pinecone(embedding, query_text=description)
        matches = self._extract_matches(pinecone_resp)
        results = [self._format_result(score, meta) for score, meta in matches]
        top_score = matches[0][0] if matches else 0.0
        result = {"results": results, "top_score": top_score}

        self._search_cache.set(cache_key, result)
        return result

    def classify_batch_ambiguous(self, ambiguous_items):
        """
        One Haiku call to classify ALL ambiguous items at once.

        Args:
            ambiguous_items: list of { description, results, top_score, index }

        Returns:
            dict mapping index → { action, results?, analysis?, question? }
        """
        if not ambiguous_items:
            return {}

        # Build a numbered list of items + their candidates for the prompt
        items_text = ""
        for item in ambiguous_items:
            candidates = "\n".join(
                f"    - {r['hts_code']}: {r['description']} "
                f"(Duty: {r['effective_duty']}, Match: {r['confidence_score']}%)"
                for r in item["results"]
            )
            items_text += (
                f"\nItem {item['index']}. \"{item['description']}\"\n"
                f"  Candidates (top match: {round(item['top_score'] * 100)}%):\n"
                f"{candidates}\n"
            )

        prompt = (
            "You are an HTS (Harmonized Tariff Schedule) classification assistant.\n\n"
            "Classify each commodity below. For each item, pick the best HTS code "
            "from its candidates, or flag it for review if truly ambiguous.\n\n"
            f"Items to classify:{items_text}\n"
            "For EACH item, respond with a JSON object containing:\n"
            '- "action": "classify" or "review"\n'
            '- "hts_code": the chosen code (if classify)\n'
            '- "analysis": brief explanation\n\n'
            "Rules:\n"
            "- hts_code MUST be one of the candidates listed for that item.\n"
            "- Prefer classifying over reviewing — only review if truly impossible to decide.\n\n"
            "Respond with ONLY a JSON array, one object per item, in order:\n"
            '[{"action": "classify", "hts_code": "XXXX.XX.XXXX", "analysis": "..."}, ...]'
        )

        response = self.anthropic.messages.create(
            model=CLAUDE_MODEL_LIGHT,
            max_tokens=200 * len(ambiguous_items),
            messages=[{"role": "user", "content": prompt}],
        )

        return self._parse_batch_response(response.content[0].text, ambiguous_items)

    def _parse_batch_response(self, text, ambiguous_items):
        """Parse Claude's JSON array response for batch classification."""
        decisions = {}
        try:
            match = re.search(r"\[.*\]", text, re.DOTALL)
            parsed = json.loads(match.group() if match else text)
            if not isinstance(parsed, list):
                parsed = []
        except (json.JSONDecodeError, AttributeError):
            parsed = []

        for i, item in enumerate(ambiguous_items):
            idx = item["index"]
            results = item["results"]

            if i < len(parsed) and parsed[i].get("action") == "classify":
                decision = parsed[i]
                target_digits = "".join(c for c in decision.get("hts_code", "") if c.isdigit())
                matched = [
                    r for r in results
                    if "".join(c for c in r["hts_code"] if c.isdigit()) == target_digits
                ]
                ordered = matched + [r for r in results if r not in matched]
                decisions[idx] = {
                    "type": "result",
                    "results": ordered[:3],
                    "analysis": decision.get("analysis", ""),
                }
            else:
                # Fallback or review — return top results
                analysis = (
                    parsed[i].get("analysis", "Classification is ambiguous — manual review recommended.")
                    if i < len(parsed) else "Classification is ambiguous — manual review recommended."
                )
                decisions[idx] = {
                    "type": "needs_review",
                    "results": results[:3],
                    "analysis": analysis,
                }

        return decisions

    # ── Stateless single-turn classification (for batch processing) ───

    def classify_single(self, description):
        """
        Classify a single commodity description without session state.
        Used by the batch invoice pipeline — each item is independent.

        Returns:
            { type: "result"|"needs_review", results: [...], analysis?: str }
        """
        embedding = self._embed(description)
        pinecone_resp = self._search_pinecone(embedding, query_text=description)
        matches = self._extract_matches(pinecone_resp)
        results = [self._format_result(score, meta) for score, meta in matches]
        top_score = matches[0][0] if matches else 0.0

        # High confidence — return directly
        if top_score >= HIGH_CONFIDENCE and results:
            return {"type": "result", "results": results[:3], "analysis": None}

        # Low confidence — ask Claude to classify or flag for review
        if not results:
            return {
                "type": "needs_review",
                "results": [],
                "analysis": "No matching HTS codes found for this commodity.",
            }

        decision = self._ask_claude_single(description, results, top_score)

        if decision["action"] == "classify":
            return {
                "type": "result",
                "results": decision["results"],
                "analysis": decision.get("analysis"),
            }

        # Claude wanted to ask a question — in batch mode, flag for review
        return {
            "type": "needs_review",
            "results": results[:3],
            "analysis": decision.get("question", "Classification is ambiguous — manual review recommended."),
        }

    def _ask_claude_single(self, description, results, top_score):
        """Single Claude call for stateless classification (no conversation history)."""
        candidates_text = "\n".join(
            f"- {r['hts_code']}: {r['description']} "
            f"(Duty: {r['effective_duty']}, Match: {r['confidence_score']}%)"
            for r in results
        )

        prompt = (
            "You are an HTS (Harmonized Tariff Schedule) classification assistant.\n\n"
            f"Commodity to classify: {description}\n\n"
            f"Vector search candidates (top match confidence: {round(top_score * 100)}%):\n"
            f"{candidates_text}\n\n"
            "Decide ONE of two actions:\n"
            "1. CLASSIFY — if you can confidently identify the correct HTS code.\n"
            "2. ASK — if you need more information to classify accurately.\n\n"
            "Rules:\n"
            "- If CLASSIFY, hts_code MUST be one of the candidates listed above.\n"
            "- If ASK, describe what additional info would help.\n\n"
            "Respond with ONLY valid JSON:\n"
            '{"action": "classify", "hts_code": "XXXX.XX.XXXX", "analysis": "Brief explanation."}\n'
            "OR\n"
            '{"action": "ask", "question": "Your clarifying question."}'
        )

        response = self.anthropic.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        return self._parse_claude_response(response.content[0].text, results)

    # ── Main entry point ──────────────────────────────────────────────

    def classify(self, session, user_message):
        """
        Process one turn of the conversation.

        session: { messages: [...], clarification_count: int }
            Mutated in place — caller (app.py) owns the session dict.

        Returns:
            { type: "result"|"question", results?: [...], question?: str, analysis?: str }
        """
        session["messages"].append({"role": "user", "content": user_message})

        # Search text = all user messages concatenated.  On follow-up turns this
        # gives the embedding the full context (e.g. "cotton t-shirts" + "knitted").
        search_text = " ".join(
            m["content"] for m in session["messages"] if m["role"] == "user"
        )

        embedding = self._embed(search_text)
        pinecone_resp = self._search_pinecone(embedding, query_text=search_text)
        matches = self._extract_matches(pinecone_resp)
        results = [self._format_result(score, meta) for score, meta in matches]
        top_score = matches[0][0] if matches else 0.0

        # ── HIGH CONFIDENCE: return directly, zero Claude calls ──────
        if top_score >= HIGH_CONFIDENCE and results:
            session["messages"].append({
                "role": "assistant",
                "content": f"Classified as {results[0]['hts_code']}",
            })
            return {"type": "result", "results": results[:3], "analysis": None}

        # ── CLARIFICATION LIMIT: present what we have ────────────────
        if session.get("clarification_count", 0) >= MAX_CLARIFICATIONS:
            session["messages"].append({
                "role": "assistant",
                "content": "Presenting best available matches.",
            })
            return {
                "type": "result",
                "results": results[:5] if results else [],
                "analysis": "The classification is ambiguous. Review the options below and select the best match for your product.",
            }

        # ── MEDIUM / LOW CONFIDENCE: one Claude call ─────────────────
        decision = self._ask_claude(session, results, top_score)

        if decision["action"] == "classify":
            session["messages"].append({
                "role": "assistant",
                "content": decision.get("analysis") or "Classification found.",
            })
            return {
                "type": "result",
                "results": decision["results"],
                "analysis": decision.get("analysis"),
            }

        # Claude decided to ask a question
        question = decision["question"]
        session["messages"].append({"role": "assistant", "content": question})
        session["clarification_count"] = session.get("clarification_count", 0) + 1
        return {"type": "question", "question": question}

    # ── Claude integration ────────────────────────────────────────────

    def _ask_claude(self, session, results, top_score):
        """
        Single Claude call.  Either picks a result from candidates or returns
        a clarifying question.  Returns:
            { action: "classify"|"ask", results?: [...], analysis?: str, question?: str }
        """
        conv_text = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in session["messages"]
        )

        candidates_text = (
            "\n".join(
                f"- {r['hts_code']}: {r['description']} "
                f"(Duty: {r['effective_duty']}, Match: {r['confidence_score']}%)"
                for r in results
            )
            if results
            else "No candidates found in the database."
        )

        prompt = (
            "You are an HTS (Harmonized Tariff Schedule) classification assistant.\n\n"
            f"Conversation so far:\n{conv_text}\n\n"
            f"Vector search candidates (top match confidence: {round(top_score * 100)}%):\n"
            f"{candidates_text}\n\n"
            "Decide ONE of two actions:\n"
            "1. CLASSIFY — if you can confidently identify the correct HTS code "
            "from the candidates above.\n"
            "2. ASK — if one specific clarifying question would meaningfully narrow "
            "the classification.\n\n"
            "Rules:\n"
            "- If CLASSIFY, hts_code MUST be one of the candidates listed above.\n"
            "- If ASK, ask about something that distinguishes the candidates: "
            "material, intended use, whether processed or raw, knitted vs woven, "
            "size category, etc. Be specific.\n"
            "- Ask at most one question.\n\n"
            "Respond with ONLY valid JSON, no other text:\n"
            '{"action": "classify", "hts_code": "XXXX.XX.XXXX", "analysis": "Brief explanation."}\n'
            "OR\n"
            '{"action": "ask", "question": "Your clarifying question."}'
        )

        response = self.anthropic.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        return self._parse_claude_response(response.content[0].text, results)

    def _parse_claude_response(self, text, results):
        """Parse Claude's JSON output, with a safe fallback."""
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            parsed = json.loads(match.group() if match else text)
        except (json.JSONDecodeError, AttributeError):
            # Fallback: return top result if available, else ask a generic question
            if results:
                return {"action": "classify", "results": results[:1],
                        "analysis": "Best match based on search results."}
            return {"action": "ask",
                    "question": "Could you describe the product in more detail — "
                                 "what material is it made of and what is it used for?"}

        if parsed.get("action") == "classify":
            # Match Claude's chosen code against our result list
            target_digits = "".join(c for c in parsed.get("hts_code", "") if c.isdigit())
            matched = [
                r for r in results
                if "".join(c for c in r["hts_code"] if c.isdigit()) == target_digits
            ]
            # Chosen result first, rest as alternatives
            ordered = matched + [r for r in results if r not in matched]
            return {
                "action": "classify",
                "results": ordered[:3],
                "analysis": parsed.get("analysis", ""),
            }

        return {
            "action": "ask",
            "question": parsed.get("question", "Could you describe the product in more detail?"),
        }
