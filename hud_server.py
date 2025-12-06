"""WebSocket server for Visual HUD communication.

Provides real-time streaming communication between Python brain and SwiftUI face.
"""

import asyncio
import json
import threading
from typing import Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import websockets
    from websockets.server import serve, WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("Warning: websockets not installed. pip install websockets")


class HUDMessageType(Enum):
    """Types of messages sent to the HUD."""
    SHOW = "show_hud"           # Show the HUD panel
    HIDE = "hide_hud"           # Hide the HUD panel
    STREAM = "stream"           # Stream content chunk
    COMPLETE = "complete"       # Stream complete
    ERROR = "error"             # Error occurred
    CLARIFY = "clarify"         # Show clarification options


class ContentType(Enum):
    """Types of content being displayed."""
    TEXT = "text"
    CODE = "code"
    LIST = "list"
    MARKDOWN = "markdown"


@dataclass
class HUDMessage:
    """Message structure for HUD communication."""
    type: str
    content: str = ""
    content_type: str = "text"
    title: str = ""
    actions: list = None  # ["copy", "insert", "run"]
    options: list = None  # For clarification: [{"label": "John Doe", "value": "john@email.com"}]

    def __post_init__(self):
        if self.actions is None:
            self.actions = []
        if self.options is None:
            self.options = []

    def to_json(self) -> str:
        return json.dumps(asdict(self))


class HUDServer:
    """WebSocket server managing HUD connections."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self._server = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._on_action_callback: Optional[Callable] = None

    def set_action_callback(self, callback: Callable[[str, dict], None]):
        """Set callback for when user clicks action buttons in HUD.

        Args:
            callback: Function(action_name, data) called when action received
        """
        self._on_action_callback = callback

    async def _handler(self, websocket: WebSocketServerProtocol):
        """Handle WebSocket connections."""
        self.clients.add(websocket)
        print(f"HUD client connected. Total clients: {len(self.clients)}")

        try:
            async for message in websocket:
                # Handle messages from HUD (action button clicks)
                try:
                    data = json.loads(message)
                    action = data.get("action")
                    if action and self._on_action_callback:
                        self._on_action_callback(action, data)
                except json.JSONDecodeError:
                    print(f"Invalid JSON from HUD: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            print(f"HUD client disconnected. Total clients: {len(self.clients)}")

    async def _broadcast(self, message: str):
        """Send message to all connected clients."""
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )

    def _send_sync(self, message: str):
        """Synchronously send a message (thread-safe)."""
        if self._loop and self._running:
            asyncio.run_coroutine_threadsafe(
                self._broadcast(message),
                self._loop
            )

    async def _run_server(self):
        """Run the WebSocket server."""
        async with serve(self._handler, self.host, self.port):
            print(f"HUD WebSocket server running on ws://{self.host}:{self.port}")
            self._running = True
            while self._running:
                await asyncio.sleep(0.1)

    def start(self):
        """Start the server in a background thread."""
        if not WEBSOCKETS_AVAILABLE:
            print("Cannot start HUD server: websockets not installed")
            return False

        def run():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            try:
                self._loop.run_until_complete(self._run_server())
            except Exception as e:
                print(f"HUD server error: {e}")
            finally:
                self._loop.close()

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Stop the server."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def is_connected(self) -> bool:
        """Check if any HUD clients are connected."""
        return len(self.clients) > 0

    # ================================================================
    # HIGH-LEVEL API FOR SENDING TO HUD
    # ================================================================

    def show(self, content: str, content_type: str = "text",
             title: str = "", actions: list = None):
        """Show content in the HUD.

        Args:
            content: The text/code/markdown to display
            content_type: "text", "code", "list", or "markdown"
            title: Optional title for the panel
            actions: List of action buttons ["copy", "insert", "run"]
        """
        msg = HUDMessage(
            type=HUDMessageType.SHOW.value,
            content=content,
            content_type=content_type,
            title=title,
            actions=actions or ["copy"]
        )
        self._send_sync(msg.to_json())

    def stream_start(self, title: str = "", content_type: str = "text",
                     actions: list = None):
        """Start streaming content to the HUD.

        Args:
            title: Optional title for the panel
            content_type: "text", "code", "list", or "markdown"
            actions: List of action buttons
        """
        msg = HUDMessage(
            type=HUDMessageType.SHOW.value,
            content="",
            content_type=content_type,
            title=title,
            actions=actions or ["copy"]
        )
        self._send_sync(msg.to_json())

    def stream_chunk(self, chunk: str):
        """Send a chunk of streaming content.

        Args:
            chunk: Text chunk to append to display
        """
        msg = HUDMessage(
            type=HUDMessageType.STREAM.value,
            content=chunk
        )
        self._send_sync(msg.to_json())

    def stream_complete(self):
        """Signal that streaming is complete."""
        msg = HUDMessage(type=HUDMessageType.COMPLETE.value)
        self._send_sync(msg.to_json())

    def hide(self):
        """Hide the HUD panel."""
        msg = HUDMessage(type=HUDMessageType.HIDE.value)
        self._send_sync(msg.to_json())

    def show_error(self, error_message: str):
        """Show an error in the HUD."""
        msg = HUDMessage(
            type=HUDMessageType.ERROR.value,
            content=error_message,
            title="Error"
        )
        self._send_sync(msg.to_json())

    def show_clarification(self, question: str, options: list):
        """Show clarification options in the HUD.

        Args:
            question: The clarification question
            options: List of dicts with "label" and "value" keys
        """
        msg = HUDMessage(
            type=HUDMessageType.CLARIFY.value,
            content=question,
            options=options
        )
        self._send_sync(msg.to_json())


# Global server instance
_hud_server: Optional[HUDServer] = None


def get_hud_server() -> HUDServer:
    """Get or create the global HUD server instance."""
    global _hud_server
    if _hud_server is None:
        _hud_server = HUDServer()
    return _hud_server


if __name__ == "__main__":
    import time

    print("Testing HUD Server")
    print("=" * 50)

    server = HUDServer()
    server.start()

    print("\nServer started. Waiting for connections...")
    print("Run the SwiftUI HUD app and it will connect.")
    print("Press Ctrl+C to stop.\n")

    try:
        # Simulate streaming content after 5 seconds
        time.sleep(5)

        if server.is_connected():
            print("Sending test content...")

            # Test streaming
            server.stream_start(title="Test Response", content_type="markdown")

            test_text = """# Hello from Python!

This is a **streaming** test.

```python
def hello():
    print("Hello, World!")
```

The response is being streamed in real-time."""

            for char in test_text:
                server.stream_chunk(char)
                time.sleep(0.02)  # Simulate LLM token delay

            server.stream_complete()
            print("Streaming complete!")
        else:
            print("No HUD clients connected.")

        # Keep running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()
        print("Done.")
