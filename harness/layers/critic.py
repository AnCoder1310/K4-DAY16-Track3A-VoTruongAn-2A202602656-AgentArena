"""Critic middleware."""

from __future__ import annotations

from harness.middleware import Middleware


class Critic(Middleware):
    name = "critic"

    def after_agent(self, ctx, report):
        claims = report.get("claims")

        if not isinstance(claims, list) or not claims:
            return report

        kept = []
        abstain = bool(report.get("abstain", False))

        for claim in claims:
            if not isinstance(claim, dict):
                continue

            text = claim.get("text")
            if not isinstance(text, str):
                continue

            if ctx.saw(text):
                kept.append(claim)
                continue

            # Handle a model-created joined claim such as:
            # "fact from doc A and fact from doc B"
            parts = text.split(" and ")

            if len(parts) == 2:
                left, right = (p.strip() for p in parts)

                left_doc = None
                right_doc = None

                for doc in ctx.corpus.docs:
                    if left in doc.body.splitlines():
                        left_doc = doc
                    if right in doc.body.splitlines():
                        right_doc = doc

                if (
                    left_doc is not None
                    and right_doc is not None
                    and left_doc.doc_id != right_doc.doc_id
                ):
                    kept.append(
                        {
                            **claim,
                            "text": left,
                            "doc_id": left_doc.doc_id,
                        }
                    )
                    kept.append(
                        {
                            **claim,
                            "text": right,
                            "doc_id": right_doc.doc_id,
                        }
                    )
                    abstain = True

        report["claims"] = kept
        report["abstain"] = abstain

        if not kept:
            report["citations"] = []
            report["abstain"] = True
            report["answer"] = (
                "Không đủ căn cứ từ các tài liệu đã quan sát để trả lời chắc chắn."
            )
        else:
            report["citations"] = sorted(
                {
                    claim["doc_id"]
                    for claim in kept
                    if claim.get("doc_id")
                }
            )

        return report
