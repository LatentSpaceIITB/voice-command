"""Response Router - Decides between TTS and Visual HUD.

The Decision Matrix:
- Short Confirmation → TTS Only ("Timer set", "Done")
- Action Execution → TTS Only ("Opening Figma")
- Information Retrieval → Visual HUD ("Summarize this")
- Code/Technical → Visual HUD ("Generate Python script")
- Clarification Needed → Both (Voice + Visual options)

Heuristic:
- If response_token_count > 30 OR content_type == "code/list" → Visual Mode
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Tuple


class OutputMode(Enum):
    """Output modality for responses."""
    TTS_ONLY = "tts"            # Voice only (confirmations, short responses)
    VISUAL_ONLY = "visual"       # HUD only (long content, code)
    BOTH = "both"                # Voice announcement + Visual content
    CLARIFY = "clarify"          # Voice question + Visual options


class ContentType(Enum):
    """Type of content being returned."""
    CONFIRMATION = "confirmation"    # "Done", "Timer set"
    ACTION = "action"                # "Opening Figma"
    TEXT = "text"                    # General text response
    CODE = "code"                    # Code snippets
    LIST = "list"                    # Lists/bullet points
    MARKDOWN = "markdown"            # Rich formatted text
    CALENDAR = "calendar"            # Calendar events
    ERROR = "error"                  # Error messages


@dataclass
class ResponseDecision:
    """Decision on how to output a response."""
    mode: OutputMode
    content_type: ContentType
    tts_message: Optional[str] = None      # What to speak (if any)
    visual_content: Optional[str] = None   # What to show in HUD (if any)
    visual_title: Optional[str] = None     # HUD panel title
    visual_actions: List[str] = None       # HUD action buttons

    def __post_init__(self):
        if self.visual_actions is None:
            self.visual_actions = []


class ResponseRouter:
    """Routes responses to appropriate output modality."""

    # Actions that should always use TTS only (confirmations)
    TTS_ONLY_ACTIONS = {
        # Fast Lane actions
        "media_play_pause", "media_next", "media_previous",
        "volume_up", "volume_down", "volume_mute", "volume_unmute",
        "lock_screen", "sleep_display",
        "wifi_on", "wifi_off", "dnd_on", "dnd_off",
        "dark_mode_on", "dark_mode_off",
        "window_maximize", "window_minimize", "window_fullscreen",
        "window_snap_left", "window_snap_right", "window_close",
        "open_app", "close_app", "switch_app", "open_url",
        "screenshot", "screenshot_selection",
        "set_timer", "set_alarm",
        # Slow Lane confirmations
        "send_email", "create_draft", "create_event",
        "create_reminder", "notion_create_page",
    }

    # Actions that should use Visual HUD
    VISUAL_ACTIONS = {
        "contextual_explain", "contextual_summarize",
        "contextual_reply", "contextual_improve", "contextual_fix",
        "search_email", "notion_search", "search_calendar",
        "generate_code", "answer_question",
    }

    # Token threshold for switching to visual
    TOKEN_THRESHOLD = 30

    # Patterns that indicate code content
    CODE_PATTERNS = [
        r"```",                     # Markdown code blocks
        r"def\s+\w+\s*\(",          # Python functions
        r"function\s+\w+\s*\(",     # JavaScript functions
        r"class\s+\w+",             # Class definitions
        r"import\s+\w+",            # Import statements
        r"const\s+\w+\s*=",         # JavaScript const
        r"let\s+\w+\s*=",           # JavaScript let
        r"var\s+\w+\s*=",           # JavaScript var
    ]

    # Patterns that indicate list content
    LIST_PATTERNS = [
        r"^\s*[-*]\s+",             # Bullet points
        r"^\s*\d+\.\s+",            # Numbered lists
        r"\n\s*[-*]\s+",            # Multi-line bullets
        r"\n\s*\d+\.\s+",           # Multi-line numbers
    ]

    def __init__(self):
        self._code_regex = [re.compile(p, re.MULTILINE) for p in self.CODE_PATTERNS]
        self._list_regex = [re.compile(p, re.MULTILINE) for p in self.LIST_PATTERNS]

    def decide(
        self,
        action: str,
        response_text: str,
        is_success: bool = True
    ) -> ResponseDecision:
        """Decide how to output a response.

        Args:
            action: The action that was executed (e.g., "open_app", "contextual_explain")
            response_text: The response text to output
            is_success: Whether the action succeeded

        Returns:
            ResponseDecision with mode, content type, and content
        """
        # Handle errors
        if not is_success:
            return self._create_error_decision(response_text)

        # Check if action is explicitly TTS-only
        if action in self.TTS_ONLY_ACTIONS:
            return self._create_tts_decision(response_text, action)

        # Check if action is explicitly visual
        if action in self.VISUAL_ACTIONS:
            return self._create_visual_decision(response_text, action)

        # Apply heuristics for unknown actions
        return self._apply_heuristics(response_text, action)

    def _apply_heuristics(self, text: str, action: str) -> ResponseDecision:
        """Apply heuristics to decide output mode."""
        content_type = self._detect_content_type(text)
        token_count = self._estimate_tokens(text)

        # Force visual for code or lists
        if content_type in (ContentType.CODE, ContentType.LIST):
            return self._create_visual_decision(text, action, content_type)

        # Force visual for long responses
        if token_count > self.TOKEN_THRESHOLD:
            return self._create_visual_decision(text, action, content_type)

        # Short non-code responses use TTS
        return self._create_tts_decision(text, action)

    def _detect_content_type(self, text: str) -> ContentType:
        """Detect the type of content in the response."""
        # Check for code patterns
        for regex in self._code_regex:
            if regex.search(text):
                return ContentType.CODE

        # Check for list patterns
        for regex in self._list_regex:
            if regex.search(text):
                return ContentType.LIST

        # Check for markdown formatting
        if any(marker in text for marker in ["##", "**", "__", "```"]):
            return ContentType.MARKDOWN

        return ContentType.TEXT

    def _estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count (words / 0.75)."""
        words = len(text.split())
        return int(words / 0.75)

    def _create_tts_decision(self, text: str, action: str) -> ResponseDecision:
        """Create a TTS-only decision."""
        return ResponseDecision(
            mode=OutputMode.TTS_ONLY,
            content_type=ContentType.CONFIRMATION if len(text) < 50 else ContentType.ACTION,
            tts_message=text,
            visual_content=None
        )

    def _create_visual_decision(
        self,
        text: str,
        action: str,
        content_type: ContentType = None
    ) -> ResponseDecision:
        """Create a visual HUD decision."""
        if content_type is None:
            content_type = self._detect_content_type(text)

        # Generate a short TTS announcement
        tts_announcement = self._generate_announcement(action, content_type)

        # Determine visual actions based on content type
        actions = self._get_visual_actions(content_type, action)

        # Generate title
        title = self._generate_title(action)

        return ResponseDecision(
            mode=OutputMode.BOTH,
            content_type=content_type,
            tts_message=tts_announcement,
            visual_content=text,
            visual_title=title,
            visual_actions=actions
        )

    def _create_error_decision(self, error_text: str) -> ResponseDecision:
        """Create an error decision."""
        return ResponseDecision(
            mode=OutputMode.TTS_ONLY,
            content_type=ContentType.ERROR,
            tts_message=error_text,
            visual_content=None
        )

    def _generate_announcement(self, action: str, content_type: ContentType) -> str:
        """Generate a short TTS announcement for visual content."""
        announcements = {
            "contextual_explain": "Here's the explanation.",
            "contextual_summarize": "Here's the summary.",
            "contextual_reply": "Here's a draft reply.",
            "contextual_improve": "Here's the improved version.",
            "contextual_fix": "Here's the fix.",
            "search_email": "Found some emails.",
            "notion_search": "Here are the results.",
            "search_calendar": "Here's your schedule.",
            "generate_code": "Here's the code.",
            "answer_question": "Here's the answer.",
        }

        if action in announcements:
            return announcements[action]

        # Generic announcements based on content type
        type_announcements = {
            ContentType.CODE: "Here's the code.",
            ContentType.LIST: "Here are the results.",
            ContentType.MARKDOWN: "Here's the information.",
        }

        return type_announcements.get(content_type, "Here you go.")

    def _get_visual_actions(self, content_type: ContentType, action: str) -> List[str]:
        """Get appropriate action buttons for the content type."""
        # Always include copy
        actions = ["copy"]

        # Add insert for certain content types
        if content_type in (ContentType.CODE, ContentType.TEXT):
            actions.append("insert")

        # Add run for code
        if content_type == ContentType.CODE:
            actions.append("run")

        # Add specific actions for certain action types
        if action == "contextual_reply":
            actions = ["copy", "insert", "send"]

        return actions

    def _generate_title(self, action: str) -> str:
        """Generate a title for the HUD panel."""
        titles = {
            "contextual_explain": "Explanation",
            "contextual_summarize": "Summary",
            "contextual_reply": "Draft Reply",
            "contextual_improve": "Improved Text",
            "contextual_fix": "Fix",
            "search_email": "Email Search",
            "notion_search": "Notion Results",
            "search_calendar": "Calendar",
            "generate_code": "Generated Code",
            "answer_question": "Answer",
        }
        return titles.get(action, "Response")

    def create_clarification(
        self,
        question: str,
        options: List[dict]
    ) -> ResponseDecision:
        """Create a clarification decision with both voice and visual.

        Args:
            question: The clarification question (e.g., "Which John?")
            options: List of options [{"label": "John Doe", "value": "john@example.com"}]
        """
        # Speak the question
        tts_message = question

        # Format options for display
        visual_content = question + "\n\n"
        for i, opt in enumerate(options, 1):
            visual_content += f"{i}. {opt['label']}\n"

        return ResponseDecision(
            mode=OutputMode.CLARIFY,
            content_type=ContentType.LIST,
            tts_message=tts_message,
            visual_content=visual_content,
            visual_title="Choose an Option",
            visual_actions=["select"]
        )


# Global router instance
response_router = ResponseRouter()


if __name__ == "__main__":
    print("Testing Response Router")
    print("=" * 50)

    router = ResponseRouter()

    # Test cases
    test_cases = [
        ("open_app", "Opening Chrome.", True),
        ("media_play_pause", "Done.", True),
        ("contextual_explain", "This error occurs because the variable `x` is undefined. You need to declare it first with `let x = 0;` before using it in the function.", True),
        ("contextual_summarize", """# Summary

The document discusses three main points:

1. **Performance**: System is 10x faster
2. **Reliability**: 99.9% uptime
3. **Cost**: 50% reduction

Overall, the upgrade is recommended.""", True),
        ("unknown_action", "Here is a short response.", True),
        ("unknown_action", "Error: Something went wrong.", False),
    ]

    for action, text, success in test_cases:
        decision = router.decide(action, text, success)
        print(f"\nAction: {action}")
        print(f"Text: {text[:50]}...")
        print(f"Decision: {decision.mode.value}")
        print(f"Content Type: {decision.content_type.value}")
        print(f"TTS: {decision.tts_message}")
        print(f"Visual Actions: {decision.visual_actions}")
