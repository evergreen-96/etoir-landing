import notify

SAMPLE = {
    "name": "Иван Петров",
    "company": "ООО Завод",
    "phone": "+79991234567",
    "email": "ivan@zavod.ru",
    "position": None,
    "comment": None,
}


def test_build_message_contains_required_fields():
    msg = notify.build_message(SAMPLE)
    assert "📬 Новая заявка с etoir.ru" in msg
    assert "Иван Петров" in msg
    assert "ООО Завод" in msg
    assert "+79991234567" in msg
    assert "ivan@zavod.ru" in msg


def test_build_message_no_none_literals():
    msg = notify.build_message(SAMPLE)
    assert "None" not in msg


def test_build_message_optional_fields_shown_when_present():
    data = {**SAMPLE, "position": "Директор", "comment": "Интересует демо"}
    msg = notify.build_message(data)
    assert "Директор" in msg
    assert "Интересует демо" in msg


def test_build_message_optional_fields_absent_when_none():
    msg = notify.build_message(SAMPLE)
    assert "Должность" not in msg
    assert "Комментарий" not in msg


import logging


def test_send_telegram_skips_if_no_token(monkeypatch, caplog):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    with caplog.at_level(logging.WARNING, logger="notify"):
        notify.send_telegram("test")
    assert "not set" in caplog.text.lower()


def test_send_telegram_calls_api_with_correct_payload(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100999")
    calls = []

    def fake_urlopen(req, timeout=None):
        calls.append({"url": req.full_url, "data": req.data, "timeout": timeout})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    notify.send_telegram("привет")

    assert len(calls) == 1
    assert "123:TOKEN" in calls[0]["url"]
    assert b"\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82" in calls[0]["data"]  # "привет" utf-8
    assert calls[0]["timeout"] == 5


def test_send_telegram_swallows_network_error(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100999")

    def fail_urlopen(req, timeout=None):
        raise OSError("network down")

    monkeypatch.setattr("urllib.request.urlopen", fail_urlopen)
    notify.send_telegram("test")  # must not raise
