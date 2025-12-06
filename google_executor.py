"""Google Super executor - handles multiple Google Workspace actions."""

from datetime import datetime, timedelta
from composio import ComposioToolSet
from config import COMPOSIO_API_KEY


class GoogleExecutor:
    """Executes Google Workspace actions via Composio Google Super."""

    def __init__(self):
        print("Initializing Google Workspace (Super)...")
        self.toolset = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        print("Google Workspace ready.")

    def execute(self, intent) -> bool:
        """Execute action(s) based on parsed intent."""
        # Handle multiple intents (array)
        if isinstance(intent, list):
            print(f"📋 Executing {len(intent)} actions...")
            success = True
            for i, single_intent in enumerate(intent, 1):
                print(f"\n--- Action {i}/{len(intent)} ---")
                if not self._execute_single(single_intent):
                    success = False
            return success
        else:
            return self._execute_single(intent)

    def _execute_single(self, intent: dict) -> bool:
        """Execute a single action."""
        action = intent.get("action")

        if action == "create_event":
            return self._create_event(intent)
        elif action == "send_email":
            return self._send_email(intent)
        elif action == "create_draft":
            return self._create_draft(intent)
        elif action == "create_doc":
            return self._create_doc(intent)
        elif action == "create_task":
            return self._create_task(intent)
        elif action == "create_reminder":
            return self._create_reminder(intent)
        elif action == "search_email":
            return self._search_email(intent)
        else:
            print(f"❌ Unsupported action: {action}")
            return False

    def _create_event(self, intent: dict) -> bool:
        """Create a calendar event."""
        try:
            start_time = intent.get("datetime")
            duration = intent.get("duration_minutes", 60)

            start_dt = datetime.fromisoformat(start_time)
            end_dt = start_dt + timedelta(minutes=duration)

            start_formatted = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
            end_formatted = end_dt.strftime("%Y-%m-%dT%H:%M:%S")

            attendees = []
            if "attendees_resolved" in intent:
                for att in intent["attendees_resolved"]:
                    if att.get("email"):
                        attendees.append(att["email"])

            print(f"📅 Creating event: {intent.get('title')}")
            print(f"   Time: {start_formatted}")
            if attendees:
                print(f"   Attendees: {', '.join(attendees)}")

            result = self.toolset.execute_action(
                action="GOOGLESUPER_CREATE_EVENT",
                params={
                    "calendar_id": "primary",
                    "summary": intent.get("title", "Untitled Event"),
                    "start_datetime": start_formatted,
                    "end_datetime": end_formatted,
                    "description": intent.get("description") or "",
                    "attendees": attendees if attendees else [],
                    "timezone": "Asia/Kolkata"
                },
                entity_id="default"
            )

            if result.get("successful"):
                print(f"✅ Event created successfully!")
                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error creating event: {e}")
            return False

    def _send_email(self, intent: dict) -> bool:
        """Send an email."""
        try:
            to = intent.get("to", [])
            if isinstance(to, str):
                to = [to]

            # Resolve recipient emails
            recipients = []
            if "recipients_resolved" in intent:
                for r in intent["recipients_resolved"]:
                    if r.get("email"):
                        recipients.append(r["email"])
            else:
                recipients = to

            print(f"📧 Sending email...")
            print(f"   To: {', '.join(recipients)}")
            print(f"   Subject: {intent.get('subject', '(no subject)')}")

            result = self.toolset.execute_action(
                action="GOOGLESUPER_SEND_EMAIL",
                params={
                    "recipient_email": recipients[0] if recipients else "",
                    "subject": intent.get("subject", ""),
                    "body": intent.get("body", ""),
                },
                entity_id="default"
            )

            if result.get("successful"):
                print(f"✅ Email sent successfully!")
                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False

    def _create_draft(self, intent: dict) -> bool:
        """Create an email draft."""
        try:
            recipients = []
            if "recipients_resolved" in intent:
                for r in intent["recipients_resolved"]:
                    if r.get("email"):
                        recipients.append(r["email"])

            print(f"📝 Creating email draft...")
            print(f"   To: {', '.join(recipients) if recipients else '(none)'}")
            print(f"   Subject: {intent.get('subject', '(no subject)')}")

            result = self.toolset.execute_action(
                action="GOOGLESUPER_CREATE_EMAIL_DRAFT",
                params={
                    "recipient_email": recipients[0] if recipients else "",
                    "subject": intent.get("subject", ""),
                    "body": intent.get("body", ""),
                },
                entity_id="default"
            )

            if result.get("successful"):
                print(f"✅ Draft created successfully!")
                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error creating draft: {e}")
            return False

    def _create_doc(self, intent: dict) -> bool:
        """Create a Google Doc."""
        try:
            title = intent.get("title", "Untitled Document")
            content = intent.get("content", "")

            print(f"📄 Creating Google Doc: {title}")

            result = self.toolset.execute_action(
                action="GOOGLESUPER_CREATE_DOCUMENT_MARKDOWN",
                params={
                    "title": title,
                    "markdown_content": content,
                },
                entity_id="default"
            )

            if result.get("successful"):
                print(f"✅ Document created successfully!")
                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error creating document: {e}")
            return False

    def _create_task(self, intent: dict) -> bool:
        """Create a Google Task."""
        try:
            title = intent.get("title", "Untitled Task")
            due_date = intent.get("due_date")

            print(f"✓ Creating task: {title}")
            if due_date:
                print(f"   Due: {due_date}")

            params = {
                "title": title,
                "tasklist_id": "@default",  # Default task list
                "status": "needsAction"     # New task status
            }
            if due_date:
                # Format as RFC3339 timestamp
                params["due"] = f"{due_date}T00:00:00Z"

            result = self.toolset.execute_action(
                action="GOOGLESUPER_INSERT_TASK",
                params=params,
                entity_id="default"
            )

            if result.get("successful"):
                print(f"✅ Task created successfully!")
                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error creating task: {e}")
            return False

    def _create_reminder(self, intent: dict) -> bool:
        """Smart reminder: calendar event if specific time, task if just date."""
        has_specific_time = intent.get("has_specific_time", False)
        title = intent.get("title", "Reminder")

        if has_specific_time:
            # Create calendar event with notification
            print(f"⏰ Creating calendar reminder (with notification)...")

            start_time = intent.get("datetime")
            if not start_time:
                print("❌ No datetime provided for timed reminder")
                return False

            start_dt = datetime.fromisoformat(start_time)
            end_dt = start_dt + timedelta(minutes=30)  # 30 min reminder event

            print(f"   Title: {title}")
            print(f"   Time: {start_dt.strftime('%Y-%m-%d %H:%M')}")

            result = self.toolset.execute_action(
                action="GOOGLESUPER_CREATE_EVENT",
                params={
                    "calendar_id": "primary",
                    "summary": f"🔔 {title}",
                    "start_datetime": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    "end_datetime": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    "description": "Created by Voice Command Tool",
                    "timezone": "Asia/Kolkata"
                },
                entity_id="default"
            )

            if result.get("successful"):
                print(f"✅ Reminder created! You'll be notified at {start_dt.strftime('%H:%M')}")
                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            # Create task (no specific time)
            print(f"📝 Creating task reminder (no specific time)...")

            date_only = intent.get("date_only")

            print(f"   Title: {title}")
            if date_only:
                print(f"   Due: {date_only}")

            params = {
                "title": title,
                "tasklist_id": "@default",
                "status": "needsAction"
            }
            if date_only:
                params["due"] = f"{date_only}T00:00:00Z"

            result = self.toolset.execute_action(
                action="GOOGLESUPER_INSERT_TASK",
                params=params,
                entity_id="default"
            )

            if result.get("successful"):
                print(f"✅ Task added to your list!")
                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False

    def _search_email(self, intent: dict) -> bool:
        """Search emails."""
        try:
            query = intent.get("query", "")
            print(f"🔍 Searching emails: {query}")

            result = self.toolset.execute_action(
                action="GOOGLESUPER_LIST_MESSAGES",
                params={
                    "q": query,
                    "max_results": 5
                },
                entity_id="default"
            )

            if result.get("successful"):
                messages = result.get("data", {}).get("messages", [])
                print(f"✅ Found {len(messages)} emails")
                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error searching emails: {e}")
            return False


if __name__ == "__main__":
    executor = GoogleExecutor()

    # Test calendar event
    test_event = {
        "action": "create_event",
        "title": "Test from Google Super",
        "datetime": (datetime.now() + timedelta(days=1, hours=2)).strftime("%Y-%m-%dT%H:%M:%S"),
        "duration_minutes": 30,
        "attendees_resolved": []
    }

    print("\nTesting Google Super executor...")
    executor.execute(test_event)
