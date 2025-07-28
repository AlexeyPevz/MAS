"""Communicator agent for the Root‑MAS platform.

The Communicator agent is responsible for interfacing with the user via
Telegram.  It listens for incoming text and voice messages, converts voice
messages to text using Yandex SpeechKit (via the `SpeechKitClient` defined in
`tools/telegram_voice.py`) and forwards user input into the MAS.  It also
handles outgoing messages by converting assistant responses into speech and
sending them back to Telegram.

This implementation is a skeleton.  The actual network interactions with
Telegram and Yandex services are left as placeholders.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional
import logging

from autogen.agentchat import ConversableAgent

from .telegram_voice import SpeechKitClient, run_telegram_bot


@dataclass
class CommunicatorConfig:
    """Configuration for the Communicator agent."""

    telegram_token: str
    speechkit_api_key: str


class CommunicatorAgent(ConversableAgent):
    """Agent that bridges the MAS with a Telegram bot."""

    def __init__(
        self,
        name: str,
        config: CommunicatorConfig,
        llm_model: str = "openrouter/gpt-4o",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # Initialise the parent ConversableAgent with a fixed model; the
        # Communicator does not perform heavy reasoning itself.
        super().__init__(name=name, llm_config={"model": llm_model}, *args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.speechkit = SpeechKitClient(api_key=config.speechkit_api_key)

    def start_bot(self) -> None:
        """Start the Telegram bot and begin listening for user messages.

        This method constructs the necessary clients and calls the
        `run_telegram_bot` function.  In a full implementation this call
        blocks until the bot is stopped.
        """
        run_telegram_bot(
            token=self.config.telegram_token,
            speechkit_client=self.speechkit,
            forward_callback=self.forward_to_groupchat,
        )

    def forward_to_groupchat(self, text: str) -> None:
        """Forward user text to the MAS group chat.

        In a full implementation this would call `self.send_message` on the
        group chat manager or publish the message to a message queue.  Here
        it is provided as a placeholder to be completed in a future sprint.
        """
        try:
            self.send(  # type: ignore[arg-type]
                {"role": "user", "content": text},
                conversation_id="groupchat",
            )
        except Exception as exc:  # pragma: no cover - runtime integration
            self.logger.error("failed to forward to group chat: %s", exc)

    def receive(self, message: dict, sender: str) -> None:  # type: ignore[override]
        """Relay assistant responses back to Telegram."""
        if sender == "groupchat" and isinstance(message, dict):
            text = message.get("content")
            if isinstance(text, str) and text:
                from .callbacks import outgoing_to_telegram

                try:
                    outgoing_to_telegram(text)
                except Exception as exc:  # pragma: no cover - runtime integration
                    self.logger.error("failed to send telegram message: %s", exc)
        super().receive(message, sender)
