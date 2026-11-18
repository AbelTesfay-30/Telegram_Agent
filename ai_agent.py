"""Gemini-powered response generation.

Wraps google-generativeai so callers get a simple async `generate()` method
with timeout and rate-limit handling. The bot must never crash because of
an AI failure — errors are caught and surfaced as a fallback string.
"""

import asyncio
import logging

import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_MODEL, SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Safety settings: block nothing aggressively — we're mimicking a human,
# but keep the defaults reasonable for a 1:1 chat bot.
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]


class AIError(Exception):
    """Raised when Gemini cannot produce a usable response."""


class AIAgent:
    """Generates human-like Telegram replies using Gemini."""

    def __init__(self) -> None:
        if not GEMINI_API_KEY:
            raise AIError("GEMINI_API_KEY is not configured")
        genai.configure(api_key=GEMINI_API_KEY)
        # temperature < 1 keeps replies varied but still coherent
        self._model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={"temperature": 0.8, "max_output_tokens": 512},
            safety_settings=SAFETY_SETTINGS,
        )

    async def generate(
        self,
        context: list[str],
        sender_name: str,
        sender_username: str,
        timeout: float = 30.0,
    ) -> str:
        """Generate a reply given the recent conversation history.

        Args:
            context: chronological list of "Name: message" lines (oldest first).
            sender_name: display name of the person we're replying to.
            sender_username: their @username (may be empty).
            timeout: max seconds to wait for the API call.

        Returns:
            The generated reply text (stripped).

        Raises:
            AIError: on timeout, rate-limit, or empty/blocked responses.
        """
        system_prompt = SYSTEM_PROMPT.format(
            name=sender_name, username=sender_username or sender_name
        )

        # Build a single prompt: system instructions + conversation transcript.
        # Gemini has no native system role via this SDK path, so we prepend it.
        transcript = "\n".join(context) if context else "(no prior messages)"
        prompt = (
            f"{system_prompt}\n\n"
            f"Recent conversation with {sender_name}:\n{transcript}\n\n"
            "Write only your next reply message. No quotes, no commentary, no emojis spam."
        )

        try:
            # generate_content is sync; run it in a thread to stay async.
            response = await asyncio.wait_for(
                asyncio.to_thread(self._model.generate_content, prompt),
                timeout=timeout,
            )
        except asyncio.TimeoutError as exc:
            raise AIError(f"Gemini request timed out after {timeout}s") from exc
        except Exception as exc:  # google.api_core errors, network issues, etc.
            # Rate limits usually surface as ResourceExhausted / 429 here.
            logger.warning("Gemini generation failed: %s", exc)
            raise AIError(f"Gemini API error: {exc}") from exc

        # Accessing .text can raise ValueError when safety filters block
        # the response — keep it inside a guarded block.
        try:
            text = (response.text or "").strip() if response else ""
        except ValueError as exc:
            raise AIError(f"Gemini blocked the response: {exc}") from exc
        if not text:
            raise AIError("Gemini returned an empty response (possibly blocked by safety filters)")
        return text
