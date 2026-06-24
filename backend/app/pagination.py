import base64
import uuid
from datetime import datetime


class CursorError(Exception):
    pass


def encode_cursor(received_at: datetime, event_id: uuid.UUID) -> str:
    return base64.urlsafe_b64encode(
        f"{received_at.isoformat()}|{event_id}".encode()
    ).decode()


def decode_cursor(token: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(token).decode()
        ts_str, id_str = raw.split("|", 1)
        cursor_ts, cursor_id = datetime.fromisoformat(ts_str), uuid.UUID(id_str)
    except ValueError as exc:
        raise CursorError from exc
    return cursor_ts, cursor_id
