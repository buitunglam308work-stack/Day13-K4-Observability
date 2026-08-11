from app.logging_config import scrub_event
from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_vietnamese_passport_number() -> None:
    passport = "C1234567"

    out = scrub_text(f"Hộ chiếu: {passport}")

    assert passport not in out
    assert "REDACTED_PASSPORT_VN" in out


def test_scrub_vietnamese_street_address() -> None:
    address = "12 Đường Nguyễn Trãi, Phường 3, Quận 5"

    out = scrub_text(f"Giao tới {address}")

    assert address not in out
    assert "REDACTED_ADDRESS_VN" in out


def test_scrub_event_redacts_nested_pii_fields() -> None:
    event = {
        "event": "request_failed",
        "session_id": "student@vinuni.edu.vn",
        "payload": {
            "contacts": ["090 123 4567", {"passport": "C1234567"}],
        },
    }

    scrubbed = scrub_event(None, "error", event)

    assert scrubbed["session_id"] == "[REDACTED_EMAIL]"
    assert scrubbed["payload"]["contacts"][0] == "[REDACTED_PHONE_VN]"
    assert scrubbed["payload"]["contacts"][1]["passport"] == "[REDACTED_PASSPORT_VN]"
