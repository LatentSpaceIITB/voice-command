from datetime import datetime, timedelta
from composio import ComposioToolSet, Action
from config import COMPOSIO_API_KEY

class CalendarExecutor:
    """Executes calendar actions via Composio Google Calendar."""

    def __init__(self):
        print("Initializing Composio Google Calendar...")
        self.toolset = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        print("Composio ready.")

    def execute(self, intent: dict) -> bool:
        """Create a calendar event from parsed intent."""
        if not intent or intent.get("action") != "create_event":
            print("❌ Invalid or unsupported intent")
            return False

        try:
            # Prepare event data
            start_time = intent.get("datetime")
            duration = intent.get("duration_minutes", 60)

            # Calculate end time
            start_dt = datetime.fromisoformat(start_time)
            end_dt = start_dt + timedelta(minutes=duration)

            # Format times for Google Calendar (RFC3339)
            start_formatted = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
            end_formatted = end_dt.strftime("%Y-%m-%dT%H:%M:%S")

            # Build attendees list
            attendees = []
            if "attendees_resolved" in intent:
                for att in intent["attendees_resolved"]:
                    if att.get("email"):
                        attendees.append(att["email"])

            # Create event using Composio
            print(f"📅 Creating event: {intent.get('title')}")
            print(f"   Time: {start_formatted}")
            if attendees:
                print(f"   Attendees: {', '.join(attendees)}")

            result = self.toolset.execute_action(
                action=Action.GOOGLECALENDAR_CREATE_EVENT,
                params={
                    "calendar_id": "primary",
                    "summary": intent.get("title", "Untitled Event"),
                    "start_datetime": start_formatted,
                    "end_datetime": end_formatted,
                    "description": intent.get("description") or "",
                    "attendees": attendees if attendees else [],
                    "timezone": "Asia/Kolkata"  # IST timezone
                },
                entity_id="default"
            )

            if result.get("successful"):
                event_data = result.get("data", {})
                event_link = event_data.get("htmlLink", "")
                print(f"✅ Event created successfully!")
                if event_link:
                    print(f"   Link: {event_link}")
                return True
            else:
                print(f"❌ Failed to create event: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error creating event: {e}")
            return False


class MockCalendarExecutor:
    """Mock executor for testing without real calendar."""

    def execute(self, intent: dict) -> bool:
        """Print what would be created instead of actually creating."""
        if not intent or intent.get("action") != "create_event":
            print("❌ Invalid or unsupported intent")
            return False

        print("\n" + "=" * 50)
        print("📅 MOCK: Would create calendar event:")
        print("=" * 50)
        print(f"   Title: {intent.get('title', 'Untitled')}")
        print(f"   When: {intent.get('datetime', 'Unknown')}")
        print(f"   Duration: {intent.get('duration_minutes', 60)} minutes")

        if "attendees_resolved" in intent:
            print("   Attendees:")
            for att in intent["attendees_resolved"]:
                email = att.get("email") or "(no email found)"
                print(f"      - {att['name']}: {email}")

        if intent.get("description"):
            print(f"   Description: {intent['description']}")

        print("=" * 50 + "\n")
        print("✅ Mock event 'created' successfully!")
        return True


if __name__ == "__main__":
    # Test with real executor
    executor = CalendarExecutor()

    test_intent = {
        "action": "create_event",
        "title": "Test Event",
        "attendees": ["test"],
        "datetime": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S"),
        "duration_minutes": 30,
        "description": "Test event from voice command",
        "attendees_resolved": []
    }

    print("\nTesting calendar executor...")
    executor.execute(test_intent)
