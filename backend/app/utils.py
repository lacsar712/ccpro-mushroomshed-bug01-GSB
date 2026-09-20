from datetime import datetime, timedelta, timezone

from flask import jsonify
from marshmallow import ValidationError

# 全局唯一一套钟：入库、滑窗、读回都以带时区的 UTC 为准。
UTC = timezone.utc


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


def utc_now() -> datetime:
    """落库瞬间与各滑窗共用的“此刻”：始终是带时区的 UTC。"""
    return datetime.now(UTC)


def normalize_datetime(value) -> datetime:
    """把入参时刻解析成带时区的 UTC datetime（与 utc_now 同一套钟）。

    - 带 Z / 显式偏移的 ISO 串：按真实偏移换算到 UTC，绝不剥掉 Z 当墙钟。
    - 无时区的串/datetime：按 UTC 处理（MySQL DATETIME 不存时区，库内统一存 UTC 墙钟）。
    """
    if isinstance(value, datetime):
        dt = value
    else:
        text = (str(value) if value is not None else "").strip()
        if not text:
            return utc_now()
        iso_text = text[:-1] + "+00:00" if text[-1:] in ("Z", "z") else text
        try:
            dt = datetime.fromisoformat(iso_text)
        except ValueError:
            dt = None
            for fmt in (
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d",
            ):
                try:
                    dt = datetime.strptime(text[:26], fmt)
                    break
                except ValueError:
                    continue
            if dt is None:
                return utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _as_utc(dt: datetime) -> datetime:
    """读回侧的统一口径：naive 值一律视为 UTC 库内墙钟，绝不拼假时区。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def dt_to_json(dt: datetime | None) -> str | None:
    """JSON 读回：UTC 真实时刻 + 真实的 Z；naive 值先按 UTC 转正。"""
    if dt is None:
        return None
    return _as_utc(dt).strftime("%Y-%m-%dT%H:%M:%SZ")


def climate_window_bounds():
    """近 24h 环境滑窗：[now-24h, now]，两个端点都用带时区 UTC。

    早于此刻 25 小时的采样落在起点之外，不进窗。
    """
    now = utc_now()
    return now - timedelta(hours=24), now


def harvest_window_start():
    """近 7 日采收窗起点：带时区 UTC，与环境窗同一套钟。"""
    return utc_now() - timedelta(days=7)


def in_last24h(dt: datetime | None) -> bool:
    """单条环境记录是否在近 24h 窗内，与 dashboard 的 climateLast24h 同源同口径。"""
    if dt is None:
        return False
    since, now = climate_window_bounds()
    return bool(since <= _as_utc(dt) <= now)
