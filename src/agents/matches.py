"""Shared validation for persisted digest matches."""


def valid_match(value) -> bool:
    if not isinstance(value, dict):
        return False
    if not all(isinstance(value.get(field), str)
               for field in ("title", "company", "description")):
        return False
    score = value.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return False
    saved_at = value.get("saved_at")
    return saved_at is None or isinstance(saved_at, str)
