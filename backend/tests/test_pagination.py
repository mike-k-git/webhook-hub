import uuid
from datetime import datetime, timezone

import pytest

from app.pagination import CursorError, decode_cursor, encode_cursor


def test_cursor_round_trip():
    ts = datetime.now(timezone.utc)
    id = uuid.uuid4()

    assert decode_cursor(encode_cursor(ts, id)) == (ts, id)


def test_decode_empty_string():
    with pytest.raises(CursorError):
        decode_cursor("")


def test_decode_invalid_base64():
    with pytest.raises(CursorError):
        decode_cursor(
            "2019-05-18T15:17:08.132263+00:00%|e43109e8-dc22-4d3d-94fd-a9d116120475"
        )


def test_decode_no_separator():
    with pytest.raises(CursorError):
        decode_cursor(
            "2019-05-18T15:17:08.132263+00:00e43109e8-dc22-4d3d-94fd-a9d116120475"
        )
