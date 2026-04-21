"""Budget-aware crawl configuration.

The agentic moment: when credits are low, the agent reduces crawl scope
to extend runtime. This is the decision a cron job can't make.
"""


def get_crawl_config(balance: float, initial: float) -> dict:
    """Determine crawl parameters based on remaining budget.

    Returns config dict with max_sources and synthesis_prompt style.

    - balance > 30% of initial: full crawl (5 sources, detailed synthesis)
    - balance 10-30%: reduced crawl (2 sources, brief synthesis)
    - balance < 10%: minimal crawl (1 source, minimal synthesis)
    """
    pct = balance / initial if initial > 0 else 1.0

    if pct < 0.10:
        return {
            "max_sources": 1,
            "synthesis_prompt": "minimal",
            "budget_mode": "critical",
            "log_message": (
                f"⚠️ budget critical — {pct*100:.0f}% remaining, "
                f"crawling 1 source with minimal synthesis"
            ),
        }
    elif pct < 0.30:
        return {
            "max_sources": 2,
            "synthesis_prompt": "brief",
            "budget_mode": "tight",
            "log_message": (
                f"budget tight — {pct*100:.0f}% remaining, "
                f"crawling 2 sources instead of 5"
            ),
        }
    else:
        return {
            "max_sources": 5,
            "synthesis_prompt": "detailed",
            "budget_mode": "normal",
            "log_message": (
                f"budget healthy — {pct*100:.0f}% remaining, "
                f"full crawl with 5 sources"
            ),
        }
