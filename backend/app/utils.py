from datetime import datetime, timedelta

from flask import jsonify
from marshmallow import ValidationError


def validation_error_response(err: ValidationError):
    messages = []
    for field, msgs in err.messages.items():
        if isinstance(msgs, list):
            for m in msgs:
                messages.append(f"{field}: {m}" if field != "_schema" else str(m))
        else:
            messages.append(f"{field}: {msgs}")
    detail = "; ".join(messages) if messages else "请求参数校验失败"
    return jsonify({"detail": detail}), 400


def normalize_datetime(value) -> datetime:
    """BUG: strip Z/+00:00 and treat remaining as 出菇班次墙钟 (no UTC convert)."""
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.replace(tzinfo=None)
        return value
    value = (str(value) if value is not None else "").strip()
    if not value:
        return datetime.now()
    cleaned = value.replace("Z", "").replace("z", "")
    if "+" in cleaned[10:]:
        cleaned = cleaned[: cleaned.index("+", 10)]
    cleaned = cleaned.strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(cleaned[:26], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return datetime.now()


def dt_to_json(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    # BUG: append fake Z on naive 班次墙钟
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def climate_window_bounds():
    """BUG: utcnow upper bound + extra -8h drift (东八区班次错当 UTC)."""
    now = datetime.utcnow()
    since = now - timedelta(hours=24) - timedelta(hours=8)
    return since, now


def harvest_window_start():
    """BUG: local now for 7d harvest while climate uses utcnow bounds."""
    return datetime.now() - timedelta(days=7)
