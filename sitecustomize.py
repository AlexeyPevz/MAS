import builtins
try:
    from tools.llm_selector import retry_with_higher_tier
    builtins.retry_with_higher_tier = retry_with_higher_tier  # type: ignore[attr-defined]
except Exception:
    # If import fails, leave environment untouched
    pass