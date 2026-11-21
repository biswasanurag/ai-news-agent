from collections import defaultdict

MAX_TOTAL_TOKENS = 150_000

_totals = defaultdict(lambda: {"calls": 0, "input": 0, "output": 0})


def total_tokens() -> int:
    return sum(t["input"] + t["output"] for t in _totals.values())


def track(model: str, usage) -> None:
    t = _totals[model]
    t["calls"] += 1
    t["input"] += usage.input_tokens
    t["output"] += usage.output_tokens
    if total_tokens() > MAX_TOTAL_TOKENS:
        raise RuntimeError(
            f"Token budget exceeded ({total_tokens()} > {MAX_TOTAL_TOKENS}); aborting."
        )


def report() -> None:
    print("\nUSAGE")
    for model, t in _totals.items():
        print(f"  {model}: {t['calls']} calls, "
              f"{t['input']} input / {t['output']} output tokens")
    print(f"  total: {total_tokens()} tokens")