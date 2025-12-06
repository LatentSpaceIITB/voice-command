"""Command router - routes intents to appropriate executors based on action type and context."""

from typing import Optional
from context_detector import ContextDetector
from google_executor import GoogleExecutor
from system_executor import SystemExecutor
from notion_executor import NotionExecutor


class CommandRouter:
    """Routes commands to appropriate executors based on action type and context."""

    # Actions handled by each executor
    GOOGLE_ACTIONS = {
        "create_event",
        "send_email",
        "create_draft",
        "create_doc",
        "create_task",
        "create_reminder",
        "search_email",
    }

    SYSTEM_ACTIONS = {
        "open_app",
        "close_app",
        "switch_app",
        "open_url",
    }

    NOTION_ACTIONS = {
        "notion_create_page",
        "notion_search",
        "notion_add_content",
    }

    def __init__(self):
        print("Initializing command router...")
        self.context_detector = ContextDetector()
        self.google_executor = GoogleExecutor()
        self.system_executor = SystemExecutor()
        self.notion_executor = NotionExecutor()
        print("Command router ready.")

    def route(self, intent) -> bool:
        """Route intent(s) to appropriate executor(s)."""
        if intent is None:
            print("❌ No intent to route")
            return False

        # Handle multiple intents (list)
        if isinstance(intent, list):
            print(f"📋 Routing {len(intent)} actions...")
            success = True
            for i, single_intent in enumerate(intent, 1):
                print(f"\n--- Action {i}/{len(intent)} ---")
                if not self._route_single(single_intent):
                    success = False
            return success
        else:
            return self._route_single(intent)

    def _route_single(self, intent: dict) -> bool:
        """Route a single intent to the appropriate executor."""
        action = intent.get("action")

        if not action:
            print("❌ No action specified in intent")
            return False

        # Get current context for potential context-aware routing
        context = self.context_detector.get_context()

        # Route to appropriate executor
        if action in self.GOOGLE_ACTIONS:
            return self.google_executor.execute(intent)

        elif action in self.SYSTEM_ACTIONS:
            return self.system_executor.execute(intent)

        elif action in self.NOTION_ACTIONS:
            return self.notion_executor.execute(intent)

        # Context-aware actions (for future expansion)
        elif action == "create_page":
            # Route based on active app
            if context["is_notion"]:
                intent["action"] = "notion_create_page"
                return self.notion_executor.execute(intent)
            else:
                # Default to Google Docs
                intent["action"] = "create_doc"
                return self.google_executor.execute(intent)

        else:
            print(f"❌ Unknown action: {action}")
            return False

    def get_context(self) -> dict:
        """Get current system context."""
        return self.context_detector.get_context()


if __name__ == "__main__":
    router = CommandRouter()

    print("\n=== Testing Command Router ===\n")

    # Test Google action
    print("Test 1: Create event (Google)")
    router.route({
        "action": "create_event",
        "title": "Test Meeting",
        "datetime": "2025-12-07T14:00:00",
        "duration_minutes": 30,
        "attendees_resolved": []
    })

    # Test system action
    print("\nTest 2: Open app (System)")
    router.route({
        "action": "open_app",
        "app_name": "Finder"
    })

    # Test multiple actions
    print("\nTest 3: Multiple actions")
    router.route([
        {"action": "open_app", "app_name": "Notes"},
        {"action": "switch_app", "app_name": "Finder"}
    ])

    # Show context
    print("\nCurrent context:")
    context = router.get_context()
    for key, value in context.items():
        print(f"  {key}: {value}")
