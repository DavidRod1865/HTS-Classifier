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
import pandas as pd
from openai import OpenAI
from pinecone import Pinecone
from anthropic import Anthropic

logger = logging.getLogger(__name__)

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "hts-codes")
EMBEDDING_MODEL = "text-embedding-3-small"
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

HIGH_CONFIDENCE = 0.82   # Return directly, no Claude call
MAX_CLARIFICATIONS = 3   # Back-and-forth limit before presenting top results


class HTSSearch:
    def __init__(self):
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = pc.Index(INDEX_NAME)
        self.hts_lookup = self._load_csv()
        logger.info(f"HTSSearch ready — {len(self.hts_lookup)} leaf nodes loaded from CSV")

    # ── CSV lookup (loaded once at startup) ──────────────────────────

    def _load_csv(self):
        """
        Load every leaf-node HTS entry into a dict keyed by HTS number.
        This is the source of truth for duty rates; Pinecone metadata is
        a secondary copy that may lag behind a CSV update.
        """
        csv_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "hts_2025_revision_13.csv"
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

    def _embed(self, text):
        resp = self.openai.embeddings.create(input=[text], model=EMBEDDING_MODEL)
        return resp.data[0].embedding

    def _search_pinecone(self, embedding, top_k=5):
        return self.index.query(vector=embedding, top_k=top_k, include_metadata=True)

    # ── Result formatting ─────────────────────────────────────────────

    @staticmethod
    def _format_hts_code(code):
        """Normalize any code string to XXXX.XX.XXXX."""
        digits = "".join(c for c in str(code) if c.isdigit())
        if len(digits) >= 10:
            return f"{digits[:4]}.{digits[4:6]}.{digits[6:10]}"
        return str(code)

    def _format_result(self, match):
        """
        Turn a Pinecone match into the dict the frontend renders.
        CSV is authoritative for duty rates; Pinecone metadata is fallback.
        """
        meta = match.metadata
        raw_code = meta.get("hts_code", "")
        csv = self.hts_lookup.get(raw_code, {})

        return {
            "hts_code": self._format_hts_code(raw_code),
            "description": csv.get("description") or meta.get("description", ""),
            "effective_duty": csv.get("general_rate") or meta.get("general_rate", ""),
            "special_duty": csv.get("special_rate") or meta.get("special_rate", ""),
            "unit": csv.get("unit") or meta.get("unit", ""),
            "confidence_score": round(match.score * 100),
            "chapter": self._format_hts_code(raw_code)[:2],
            "match_type": "vector_search",
            "duty_source": "usitc",
        }

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
        pinecone_resp = self._search_pinecone(embedding)

        results = (
            [self._format_result(m) for m in pinecone_resp.matches]
            if pinecone_resp.matches else []
        )
        top_score = pinecone_resp.matches[0].score if pinecone_resp.matches else 0.0

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
