"""Notion executor - handles Notion workspace actions via Composio."""

from composio import ComposioToolSet
from config import COMPOSIO_API_KEY


class NotionExecutor:
    """Executes Notion actions via Composio."""

    # Default parent page for new pages (can be configured)
    DEFAULT_PARENT_ID = None  # Will be set dynamically

    def __init__(self):
        print("Initializing Notion...")
        self.toolset = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        self._cache_workspace_root()
        print("Notion ready.")

    def _cache_workspace_root(self):
        """Find and cache a default parent page for new pages."""
        try:
            result = self.toolset.execute_action(
                action='NOTION_SEARCH_NOTION_PAGE',
                params={'query': '', 'page_size': 5},
                entity_id='default'
            )
            if result.get('successful'):
                results = result.get('data', {}).get('results', [])
                for item in results:
                    if item.get('object') == 'page':
                        self.DEFAULT_PARENT_ID = item.get('id')
                        break
        except Exception:
            pass

    def execute(self, intent: dict) -> bool:
        """Execute Notion action based on intent."""
        action = intent.get("action")

        if action == "notion_create_page":
            return self._create_page(intent)
        elif action == "notion_search":
            return self._search_pages(intent)
        elif action == "notion_add_content":
            return self._add_content(intent)
        else:
            print(f"❌ Unknown Notion action: {action}")
            return False

    def _create_page(self, intent: dict) -> bool:
        """Create a new Notion page."""
        try:
            title = intent.get("title", "Untitled")
            parent_id = intent.get("parent_id") or self.DEFAULT_PARENT_ID

            if not parent_id:
                print("❌ No parent page found. Please specify a parent_id.")
                return False

            print(f"📄 Creating Notion page: {title}")

            result = self.toolset.execute_action(
                action='NOTION_CREATE_NOTION_PAGE',
                params={
                    'parent_id': parent_id,
                    'title': title
                },
                entity_id='default'
            )

            if result.get('successful'):
                page_data = result.get('data', {})
                page_url = page_data.get('url', '')
                print(f"✅ Page created: {title}")
                if page_url:
                    print(f"   URL: {page_url}")
                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error creating page: {e}")
            return False

    def _search_pages(self, intent: dict) -> bool:
        """Search Notion pages."""
        try:
            query = intent.get("query", "")
            print(f"🔍 Searching Notion for: '{query}'")

            result = self.toolset.execute_action(
                action='NOTION_SEARCH_NOTION_PAGE',
                params={
                    'query': query,
                    'page_size': 5
                },
                entity_id='default'
            )

            if result.get('successful'):
                results = result.get('data', {}).get('results', [])
                print(f"✅ Found {len(results)} results:")

                for item in results:
                    obj_type = item.get('object', 'unknown')

                    # Extract title
                    if obj_type == 'page':
                        props = item.get('properties', {})
                        title_prop = props.get('title', props.get('Name', {}))
                        if 'title' in title_prop and title_prop['title']:
                            title = title_prop['title'][0].get('plain_text', 'Untitled')
                        else:
                            title = 'Untitled'
                    elif obj_type == 'database':
                        title_list = item.get('title', [])
                        title = title_list[0].get('plain_text', 'Untitled DB') if title_list else 'Untitled DB'
                    else:
                        title = 'Unknown'

                    print(f"   • [{obj_type}] {title}")

                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error searching: {e}")
            return False

    def _add_content(self, intent: dict) -> bool:
        """Add content to a Notion page."""
        try:
            page_id = intent.get("page_id")
            content = intent.get("content", "")

            if not page_id:
                print("❌ No page_id specified")
                return False

            print(f"📝 Adding content to page...")

            result = self.toolset.execute_action(
                action='NOTION_ADD_MULTIPLE_PAGE_CONTENT',
                params={
                    'page_id': page_id,
                    'content_blocks': [
                        {
                            'type': 'paragraph',
                            'paragraph': {
                                'rich_text': [{'type': 'text', 'text': {'content': content}}]
                            }
                        }
                    ]
                },
                entity_id='default'
            )

            if result.get('successful'):
                print(f"✅ Content added!")
                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error adding content: {e}")
            return False


if __name__ == "__main__":
    executor = NotionExecutor()

    print("\n=== Testing Notion Executor ===\n")

    # Test search
    print("Test 1: Search pages")
    executor.execute({
        "action": "notion_search",
        "query": "Getting Started"
    })

    # Test create page
    print("\nTest 2: Create page")
    executor.execute({
        "action": "notion_create_page",
        "title": "Test Page from Voice Command"
    })
