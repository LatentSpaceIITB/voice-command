import json
from datetime import datetime, timedelta
from typing import Optional
from difflib import get_close_matches
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, CONTACTS_FILE


class IntentParser:
    """Parses natural language commands into structured intents for Google Workspace and system control."""

    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.contacts = self._load_contacts()

    def _load_contacts(self) -> dict:
        """Load contacts mapping from JSON file."""
        try:
            with open(CONTACTS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {CONTACTS_FILE} not found. Using empty contacts.")
            return {}

    def parse(self, text: str) -> Optional[dict]:
        """Parse natural language text into a structured intent."""
        if not text.strip():
            return None

        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        prompt = f"""You are a voice assistant that can control Google Workspace and macOS system. Parse the voice command into a structured JSON action.

Current date: {current_date}
Current time: {current_time}
Tomorrow's date: {tomorrow}

Voice command: "{text}"

Determine the action type and extract relevant information. Return ONLY valid JSON (no markdown, no explanation).

SUPPORTED ACTIONS:

1. CREATE CALENDAR EVENT:
{{
    "action": "create_event",
    "title": "event title",
    "attendees": ["list of names mentioned"],
    "datetime": "YYYY-MM-DDTHH:MM:SS",
    "duration_minutes": 60,
    "description": "optional details"
}}

2. SEND EMAIL:
{{
    "action": "send_email",
    "to": ["recipient names"],
    "subject": "email subject",
    "body": "email content"
}}

3. CREATE EMAIL DRAFT:
{{
    "action": "create_draft",
    "to": ["recipient names"],
    "subject": "email subject",
    "body": "email content"
}}

4. CREATE GOOGLE DOC:
{{
    "action": "create_doc",
    "title": "document title",
    "content": "initial content or empty string"
}}

5. CREATE REMINDER (smart detection):
{{
    "action": "create_reminder",
    "title": "reminder description",
    "datetime": "YYYY-MM-DDTHH:MM:SS or null if no specific time",
    "date_only": "YYYY-MM-DD if only date mentioned, null if specific time given",
    "has_specific_time": true/false
}}

6. SEARCH EMAIL:
{{
    "action": "search_email",
    "query": "search query"
}}

7. OPEN APPLICATION:
{{
    "action": "open_app",
    "app_name": "application name"
}}

8. CLOSE APPLICATION:
{{
    "action": "close_app",
    "app_name": "application name"
}}

9. SWITCH TO APPLICATION:
{{
    "action": "switch_app",
    "app_name": "application name"
}}

10. OPEN URL/WEBSITE:
{{
    "action": "open_url",
    "url": "website URL"
}}

11. CREATE NOTION PAGE:
{{
    "action": "notion_create_page",
    "title": "page title"
}}

12. SEARCH NOTION:
{{
    "action": "notion_search",
    "query": "search query"
}}

PARSING RULES:
- "tomorrow" = {tomorrow}
- "8 pm" or "8:00 pm" = 20:00:00
- "morning" = 09:00:00, "afternoon" = 14:00:00, "evening" = 18:00:00
- "heading" or "title" in calendar context = event title
- "Set calendar to [person]" = create event with that person as attendee
- "Email [person]" or "Send email to [person]" = send_email action
- "Draft email" or "Create draft" = create_draft action
- "Create doc" or "New document" = create_doc action
- "Remind me" or "Add task" = create_reminder action
  - If specific time given (e.g., "at 3pm", "at 10:30") → has_specific_time: true
  - If only date given (e.g., "tomorrow", "next Monday") → has_specific_time: false
- "Find emails" or "Search for emails" = search_email action
- "Open [app]" or "Launch [app]" or "Start [app]" = open_app action
- "Close [app]" or "Quit [app]" or "Exit [app]" = close_app action
- "Switch to [app]" or "Go to [app]" = switch_app action
- "Open [website]" or "Go to [website]" = open_url action (extract domain/URL)
- "Create Notion page" or "New page in Notion" or "Create page called X" = notion_create_page
- "Search Notion for X" or "Find in Notion" = notion_search

Return ONLY the JSON object."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            response_text = response.content[0].text.strip()
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            intent = json.loads(response_text)

            # Handle multiple intents (list) or single intent
            if isinstance(intent, list):
                for single_intent in intent:
                    self._resolve_contacts(single_intent)
            else:
                self._resolve_contacts(intent)

            print(f"🧠 Parsed intent: {json.dumps(intent, indent=2)}")
            return intent

        except json.JSONDecodeError as e:
            print(f"Failed to parse Claude response: {e}")
            print(f"Response was: {response.content[0].text}")
            return None

    def _fuzzy_match_contact(self, name: str) -> tuple:
        """Find best matching contact using fuzzy matching.
        Returns (matched_name, email) or (original_name, None) if no match."""
        name_lower = name.lower()

        # Exact match first
        if name_lower in self.contacts:
            return (name, self.contacts[name_lower])

        # Fuzzy match - find closest name
        contact_names = list(self.contacts.keys())
        matches = get_close_matches(name_lower, contact_names, n=1, cutoff=0.6)

        if matches:
            matched_name = matches[0]
            print(f"   🔍 Fuzzy matched '{name}' → '{matched_name}'")
            return (matched_name.title(), self.contacts[matched_name])

        return (name, None)

    def _resolve_contacts(self, intent: dict):
        """Resolve names to emails using contacts file with fuzzy matching."""
        # For calendar events
        if "attendees" in intent and intent["attendees"]:
            resolved = []
            for name in intent["attendees"]:
                matched_name, email = self._fuzzy_match_contact(name)
                resolved.append({"name": matched_name, "email": email})
            intent["attendees_resolved"] = resolved

        # For emails
        if "to" in intent and intent["to"]:
            resolved = []
            for name in intent["to"]:
                matched_name, email = self._fuzzy_match_contact(name)
                resolved.append({"name": matched_name, "email": email})
            intent["recipients_resolved"] = resolved


if __name__ == "__main__":
    parser = IntentParser()

    test_commands = [
        "Set calendar to Navyansh tomorrow 8:00 pm with heading Gameramp.io",
        "Send email to Suraj about the project update",
        "Create a draft email to Navyansh with subject Meeting Notes",
        "Create a new document called Project Ideas",
        "Remind me to call the client tomorrow",
        "Find emails from last week about the budget",
    ]

    for cmd in test_commands:
        print(f"\n{'='*50}")
        print(f"Command: {cmd}")
        print('='*50)
        result = parser.parse(cmd)
        print()
