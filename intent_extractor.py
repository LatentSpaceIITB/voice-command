"""Fast local parameter extraction for Fast Lane commands.

This module extracts parameters from transcribed text without using an LLM.
Uses regex patterns and keyword matching for speed.
"""

import re
from typing import Optional
from system_executor import APP_ALIASES


class IntentExtractor:
    """Extract parameters from transcribed text for Fast Lane commands."""

    # Common URL patterns
    URL_KEYWORDS = {
        "gmail": "https://mail.google.com",
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "github": "https://github.com",
        "twitter": "https://twitter.com",
        "x": "https://x.com",
        "linkedin": "https://linkedin.com",
        "facebook": "https://facebook.com",
        "reddit": "https://reddit.com",
        "stackoverflow": "https://stackoverflow.com",
        "amazon": "https://amazon.com",
        "netflix": "https://netflix.com",
    }

    def extract_app_name(self, text: str) -> Optional[str]:
        """Extract application name from command text.

        Examples:
            "open chrome" -> "chrome"
            "close spotify" -> "spotify"
            "switch to finder" -> "finder"
            "quit vscode" -> "vscode"
        """
        text_lower = text.lower().strip()

        # Patterns to try (in order of specificity)
        patterns = [
            r"(?:open|launch|start|run)\s+(?:the\s+)?(.+?)(?:\s+app)?$",
            r"(?:close|quit|exit|kill)\s+(?:the\s+)?(.+?)(?:\s+app)?$",
            r"(?:switch\s+to|go\s+to|focus|bring\s+up)\s+(?:the\s+)?(.+?)$",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                app_name = match.group(1).strip()
                # Check if it's a known alias
                if app_name in APP_ALIASES:
                    return app_name
                # Try to find a partial match
                for alias in APP_ALIASES:
                    if alias in app_name or app_name in alias:
                        return alias
                return app_name

        return None

    def extract_timer_duration(self, text: str) -> Optional[int]:
        """Extract timer duration in seconds from command text.

        Examples:
            "timer for 5 minutes" -> 300
            "set timer 30 seconds" -> 30
            "timer for 1 hour" -> 3600
            "10 minute timer" -> 600
        """
        text_lower = text.lower().strip()

        # Try different patterns
        patterns = [
            # "timer for X minutes/seconds/hours"
            r"timer\s+(?:for\s+)?(\d+)\s*(min(?:ute)?s?|sec(?:ond)?s?|hour?s?)",
            # "X minute/second/hour timer"
            r"(\d+)\s*(min(?:ute)?s?|sec(?:ond)?s?|hour?s?)\s+timer",
            # "set timer X minutes"
            r"set\s+(?:a\s+)?timer\s+(?:for\s+)?(\d+)\s*(min(?:ute)?s?|sec(?:ond)?s?|hour?s?)",
            # "start a X minute timer"
            r"start\s+(?:a\s+)?(\d+)\s*(min(?:ute)?s?|sec(?:ond)?s?|hour?s?)\s+timer",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = int(match.group(1))
                unit = match.group(2).lower()

                if unit.startswith("sec"):
                    return value
                elif unit.startswith("min"):
                    return value * 60
                elif unit.startswith("hour"):
                    return value * 3600

        return None

    def extract_alarm_time(self, text: str) -> Optional[str]:
        """Extract alarm time from command text.

        Examples:
            "alarm at 7am" -> "7:00 AM"
            "alarm for 10:30pm" -> "10:30 PM"
            "wake me up at 6" -> "6:00 AM"
        """
        text_lower = text.lower().strip()

        # Patterns for time extraction
        patterns = [
            # "at 7:30am" or "at 7:30 am"
            r"(?:at|for)\s+(\d{1,2}):?(\d{2})?\s*(am|pm)",
            # "at 7" (assume AM if just number)
            r"(?:at|for)\s+(\d{1,2})(?:\s+(am|pm))?",
            # "wake me up at 7"
            r"wake\s+(?:me\s+)?up\s+(?:at\s+)?(\d{1,2}):?(\d{2})?\s*(am|pm)?",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                hour = int(groups[0])

                # Handle minutes
                if len(groups) > 1 and groups[1] and groups[1].isdigit():
                    minutes = int(groups[1])
                else:
                    minutes = 0

                # Handle AM/PM
                period = None
                for g in groups:
                    if g and g.lower() in ("am", "pm"):
                        period = g.upper()
                        break

                # Default to AM if no period specified and hour < 12
                if not period:
                    period = "AM" if hour < 12 else "PM"

                return f"{hour}:{minutes:02d} {period}"

        return None

    def extract_url(self, text: str) -> Optional[str]:
        """Extract URL from command text.

        Examples:
            "go to gmail" -> "https://mail.google.com"
            "open youtube" -> "https://www.youtube.com"
            "go to google.com" -> "https://google.com"
        """
        text_lower = text.lower().strip()

        # Check for known URL keywords
        for keyword, url in self.URL_KEYWORDS.items():
            if keyword in text_lower:
                return url

        # Check for explicit .com, .org, etc.
        url_pattern = r"(?:go\s+to|open)\s+([a-z0-9\-]+\.(?:com|org|net|io|dev|ai))"
        match = re.search(url_pattern, text_lower)
        if match:
            domain = match.group(1)
            return f"https://{domain}"

        return None

    def extract_volume_level(self, text: str) -> Optional[int]:
        """Extract volume level from command text.

        Examples:
            "volume to 50" -> 50
            "set volume 80" -> 80
            "volume at 30 percent" -> 30
        """
        text_lower = text.lower().strip()

        patterns = [
            r"volume\s+(?:to|at)?\s*(\d+)(?:\s*percent)?",
            r"set\s+volume\s+(?:to\s+)?(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                level = int(match.group(1))
                # Clamp to valid range
                return max(0, min(100, level))

        return None

    def extract_for_action(self, action: str, text: str) -> dict:
        """Extract relevant parameters based on action type.

        Returns a dict with extracted parameters for the given action.
        """
        result = {"action": action}

        if action in ("open_app", "close_app", "switch_app"):
            app_name = self.extract_app_name(text)
            if app_name:
                result["app_name"] = app_name

        elif action == "open_url":
            url = self.extract_url(text)
            if url:
                result["url"] = url

        elif action == "set_timer":
            duration = self.extract_timer_duration(text)
            if duration:
                result["duration_seconds"] = duration

        elif action == "set_alarm":
            alarm_time = self.extract_alarm_time(text)
            if alarm_time:
                result["time"] = alarm_time

        elif action in ("volume_up", "volume_down"):
            # Optional: extract specific level
            level = self.extract_volume_level(text)
            if level:
                result["level"] = level

        return result


# Global instance
intent_extractor = IntentExtractor()


if __name__ == "__main__":
    # Test cases
    extractor = IntentExtractor()

    print("Testing app name extraction:")
    test_cases = [
        "open chrome",
        "close spotify",
        "switch to finder",
        "quit vscode",
        "launch terminal",
    ]
    for test in test_cases:
        print(f"  '{test}' -> {extractor.extract_app_name(test)}")

    print("\nTesting timer duration extraction:")
    test_cases = [
        "timer for 5 minutes",
        "set timer 30 seconds",
        "timer for 1 hour",
        "10 minute timer",
        "start a 15 minute timer",
    ]
    for test in test_cases:
        duration = extractor.extract_timer_duration(test)
        print(f"  '{test}' -> {duration} seconds")

    print("\nTesting alarm time extraction:")
    test_cases = [
        "alarm at 7am",
        "alarm for 10:30pm",
        "wake me up at 6",
        "set alarm 9am",
    ]
    for test in test_cases:
        print(f"  '{test}' -> {extractor.extract_alarm_time(test)}")

    print("\nTesting URL extraction:")
    test_cases = [
        "go to gmail",
        "open youtube",
        "go to google.com",
    ]
    for test in test_cases:
        print(f"  '{test}' -> {extractor.extract_url(test)}")
