from datetime import datetime, timedelta, timezone

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


def utcnow() -> datetime:
    """全系统唯一时钟: 朴素 UTC (MySQL DATETIME 不存时区, 读回即此基准)。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_datetime(value) -> datetime:
    """把任意 ISO-8601 输入解析到唯一时钟 (朴素 UTC)。

    带 Z/偏移的按真实瞬间换算到 UTC; 不带偏移的视为同一套 UTC 钟。
    """
    if isinstance(value, datetime):
        dt = value
    else:
        text = (str(value) if value is not None else "").strip()
        if not text:
            return utcnow()
        candidate = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
        try:
            dt = datetime.fromisoformat(candidate)
        except ValueError:
            dt = None
            for fmt in (
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d",
            ):
                try:
                    dt = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    continue
            if dt is None:
                return utcnow()
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def dt_to_json(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    # 与入库同一套钟: 朴素 UTC 序列化, Z 是真实 UTC 标记而非拼贴
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def climate_window_bounds():
    """24h 滑动窗: [utcnow-24h, utcnow], 与落库时钟同源。"""
    now = utcnow()
    since = now - timedelta(hours=24)
    return since, now


def harvest_window_start():
    """7 日公斤窗, 与环境窗同一套 UTC 钟。"""
    return utcnow() - timedelta(days=7)
