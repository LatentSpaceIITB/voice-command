"""Streaming Handler - Streams Claude responses to HUD in real-time.

Pipes LLM tokens directly to the Visual HUD as they arrive,
providing sub-second time to first visible content.
"""

from typing import Optional, Callable, Generator
from anthropic import Anthropic
from hud_server import get_hud_server, HUDServer
from response_router import ResponseRouter, ResponseDecision, OutputMode


class StreamingHandler:
    """Handles streaming responses from Claude to the HUD."""

    def __init__(self, hud_server: Optional[HUDServer] = None):
        self.client = Anthropic()
        self.hud = hud_server or get_hud_server()
        self.router = ResponseRouter()

    def stream_response(
        self,
        prompt: str,
        action: str,
        system_prompt: str = None,
        on_complete: Callable[[str], None] = None
    ) -> str:
        """Stream a Claude response to the HUD.

        Args:
            prompt: The user prompt to send to Claude
            action: The action type (for routing decision)
            system_prompt: Optional system prompt
            on_complete: Callback with full response when done

        Returns:
            The complete response text
        """
        # Prepare the request
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1024,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        # Get title and content type for the HUD
        title = self._get_title(action)
        content_type = self._get_content_type(action)
        actions = self._get_actions(action)

        # Start streaming to HUD
        self.hud.stream_start(
            title=title,
            content_type=content_type,
            actions=actions
        )

        full_response = ""

        try:
            # Stream from Claude
            with self.client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    full_response += text
                    self.hud.stream_chunk(text)

            # Signal completion
            self.hud.stream_complete()

            if on_complete:
                on_complete(full_response)

            return full_response

        except Exception as e:
            self.hud.show_error(str(e))
            raise

    def stream_contextual(
        self,
        action: str,
        context_content: str,
        context_app: str = "",
        context_is_image: bool = False,
        image_data: str = None
    ) -> str:
        """Stream a contextual command response.

        Args:
            action: The contextual action (e.g., "contextual_explain")
            context_content: The captured context (text or base64 image)
            context_app: The app the context came from
            context_is_image: Whether context is an image
            image_data: Base64 image data (if image)

        Returns:
            The complete response text
        """
        # Build the task prompt
        task = self._get_contextual_task(action)

        # Get HUD display info
        title = self._get_title(action)
        content_type = self._get_content_type(action)
        actions = self._get_actions(action)

        # Start streaming to HUD
        self.hud.stream_start(
            title=title,
            content_type=content_type,
            actions=actions
        )

        full_response = ""

        try:
            if context_is_image and image_data:
                # Use vision model for images
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": f"{task}\n\nContext: From {context_app}"
                            }
                        ],
                    }]
                )
                # Vision doesn't stream, but we can still show in HUD
                full_response = response.content[0].text
                self.hud.stream_chunk(full_response)
            else:
                # Stream text response
                prompt = f"{task}\n\n{context_content}\n\nContext: From {context_app}"

                with self.client.messages.stream(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                ) as stream:
                    for text in stream.text_stream:
                        full_response += text
                        self.hud.stream_chunk(text)

            self.hud.stream_complete()
            return full_response

        except Exception as e:
            self.hud.show_error(str(e))
            raise

    def _get_contextual_task(self, action: str) -> str:
        """Get the task prompt for a contextual action."""
        tasks = {
            "contextual_explain": "Explain the following in simple terms:",
            "contextual_summarize": "Summarize the following concisely:",
            "contextual_reply": "Draft a professional reply to the following:",
            "contextual_improve": "Improve and polish the following text:",
            "contextual_fix": "Identify and explain how to fix the error in:",
        }
        return tasks.get(action, "Process this:")

    def _get_title(self, action: str) -> str:
        """Get HUD title for action."""
        titles = {
            "contextual_explain": "Explanation",
            "contextual_summarize": "Summary",
            "contextual_reply": "Draft Reply",
            "contextual_improve": "Improved Text",
            "contextual_fix": "Fix",
            "search_email": "Email Search",
            "notion_search": "Notion Results",
            "search_calendar": "Calendar",
            "answer_question": "Answer",
        }
        return titles.get(action, "Response")

    def _get_content_type(self, action: str) -> str:
        """Get content type for action."""
        code_actions = {"contextual_fix", "generate_code"}
        if action in code_actions:
            return "code"
        return "markdown"

    def _get_actions(self, action: str) -> list:
        """Get action buttons for the content."""
        base = ["copy"]

        if action in {"contextual_reply", "contextual_improve"}:
            return ["copy", "insert"]
        elif action in {"contextual_fix", "generate_code"}:
            return ["copy", "insert", "run"]

        return base


# Convenience function for simple streaming
def stream_to_hud(
    prompt: str,
    action: str = "answer_question",
    system_prompt: str = None
) -> str:
    """Stream a Claude response to the HUD.

    Args:
        prompt: The user prompt
        action: Action type for routing
        system_prompt: Optional system prompt

    Returns:
        Complete response text
    """
    handler = StreamingHandler()
    return handler.stream_response(prompt, action, system_prompt)


if __name__ == "__main__":
    import time
    from hud_server import HUDServer

    print("Testing Streaming Handler")
    print("=" * 50)

    # Start HUD server
    server = HUDServer()
    server.start()

    print("Waiting for HUD connection...")
    time.sleep(3)

    if not server.is_connected():
        print("No HUD connected. Start the VoiceHUD app first.")
        exit(1)

    # Create handler
    handler = StreamingHandler(hud_server=server)

    # Test streaming
    print("\nStreaming test response...")

    response = handler.stream_response(
        prompt="Explain what a Python decorator is in 3 sentences.",
        action="contextual_explain"
    )

    print(f"\nFull response:\n{response}")

    # Keep server running
    print("\nPress Ctrl+C to exit...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
