from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from src.provenance.evidence import (
    Evidence,
    EvidenceBundle,
)


def news_article_to_evidence(
    article: Dict[str, Any],
) -> Evidence:

    article_id = article.get(
        "article_id",
        "unknown",
    )

    ticker = article.get(
        "ticker"
    )

    event_id = article.get(
        "event_id"
    )

    source = article.get(
        "source",
        "synthetic_news",
    )

    content = {
        "headline": article.get(
            "headline"
        ),

        "summary": article.get(
            "summary"
        ),

        "body": article.get(
            "body"
        ),

        "publication_datetime": article.get(
            "publication_datetime"
        ),

        "event_datetime": article.get(
            "event_datetime"
        ),

        "sentiment": article.get(
            "sentiment"
        ),

        "article_type": article.get(
            "article_type"
        ),

        "author": article.get(
            "author"
        ),

        "tags": article.get(
            "tags",
            [],
        ),

        "entities": article.get(
            "entities",
            [],
        ),
    }

    return Evidence(
        source_type="news",

        source=source,

        locator=f"article_id={article_id}",

        content_type="news_article",

        content=content,

        ticker=ticker,

        event_id=event_id,

        source_system=(
            "synthetic_news_store"
        ),

        synthetic=True,

        metadata={
            "article_id": article_id,
            "headline": article.get(
                "headline"
            ),
        },

        provenance={
            "retrieval_method": (
                "direct_news_store"
            ),
            "publication_datetime": article.get(
                "publication_datetime"
            ),
        },
    )


def news_articles_to_evidence(
    articles: Iterable[
        Dict[str, Any]
    ],
) -> EvidenceBundle:

    bundle = EvidenceBundle()

    for article in articles:

        bundle.add(
            news_article_to_evidence(
                article
            )
        )

    return bundle