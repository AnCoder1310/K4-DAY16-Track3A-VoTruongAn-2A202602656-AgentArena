"""Citation checker middleware."""

from __future__ import annotations

from harness.middleware import Middleware


class CitationChecker(Middleware):
    name = "citation_checker"

    def after_agent(self, ctx, report):
        claims = report.get("claims")
        if not isinstance(claims, list) or ctx.corpus is None:
            return report

        def line_supports(doc, text):
            return any(text in line for line in doc.body.splitlines())

        for claim in claims:
            if not isinstance(claim, dict):
                continue

            text = claim.get("text")
            doc_id = claim.get("doc_id")

            if not isinstance(text, str):
                continue

            current = ctx.corpus.get(doc_id) if doc_id else None

            if current is not None and line_supports(current, text):
                continue

            for doc in ctx.corpus.docs:
                if doc.body in ctx.observed_text and line_supports(doc, text):
                    claim["doc_id"] = doc.doc_id
                    break

        report["citations"] = sorted(
            {
                claim["doc_id"]
                for claim in claims
                if isinstance(claim, dict) and claim.get("doc_id")
            }
        )

        return report
