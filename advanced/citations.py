"""Citation policy used by round 2; no benchmark data is consulted."""


def full_page_citations(citations):
    """Keep the model's proposed box for audit while citing the original full page.

    A full-page box is imprecise, so it must be paired with a specific label and
    quotation. Whether the page actually supports the answer is reviewed separately.
    """
    return [dict(c, model_bbox=c['bbox'], bbox=[0, 0, 1, 1]) for c in citations]
