import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / 'root_mas' / 'root_mas'))

from tools import telegram_voice


def test_run_telegram_bot(monkeypatch):
    called = {"run": False}

    class DummyBot:
        def __init__(self, token, speechkit_client=None):
            assert token == "abc"
            assert speechkit_client == "client"

        def run(self):
            called["run"] = True

    monkeypatch.setattr(telegram_voice, "TelegramVoiceBot", DummyBot)
    telegram_voice.run_telegram_bot("abc", speechkit_client="client")
    assert called["run"]
