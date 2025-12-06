#!/usr/bin/env python3
"""Test script for Visual HUD.

Run this to test the HUD without the full voice command pipeline.
Make sure to build and run VoiceHUD.app first.
"""

import time
from hud_server import HUDServer


def main():
    print("Visual HUD Test")
    print("=" * 50)
    print()

    # Start WebSocket server
    server = HUDServer()
    server.start()

    print("WebSocket server started on ws://localhost:8765")
    print()
    print("Now start VoiceHUD.app and wait for connection...")
    print()

    # Wait for connection
    for i in range(30):
        if server.is_connected():
            break
        print(f"Waiting for HUD connection... ({30-i}s)")
        time.sleep(1)

    if not server.is_connected():
        print("No HUD client connected after 30 seconds.")
        print("Make sure VoiceHUD.app is running.")
        return

    print("HUD connected!")
    print()

    # Test 1: Simple text display
    print("Test 1: Showing simple text...")
    server.show(
        content="Hello from Python! This is a test of the Visual HUD.",
        content_type="text",
        title="Test Message",
        actions=["copy"]
    )
    time.sleep(3)

    # Test 2: Streaming text
    print("Test 2: Streaming markdown content...")
    server.stream_start(title="Streaming Test", content_type="markdown", actions=["copy", "insert"])

    test_content = """# Streaming Response

This text is being **streamed** in real-time from Python.

## Key Points

1. WebSocket connection is working
2. Content streams character by character
3. HUD updates in real-time

```python
def hello():
    print("Hello, World!")
```

*This simulates Claude's streaming API output.*
"""

    for char in test_content:
        server.stream_chunk(char)
        time.sleep(0.01)  # 10ms per character

    server.stream_complete()
    print("Streaming complete!")
    time.sleep(3)

    # Test 3: Code block
    print("Test 3: Showing code block...")
    code = '''def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate first 10 Fibonacci numbers
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")'''

    server.show(
        content=code,
        content_type="code",
        title="Generated Code",
        actions=["copy", "insert", "run"]
    )
    time.sleep(3)

    # Test 4: Clarification
    print("Test 4: Showing clarification dialog...")
    server.show_clarification(
        question="Which John did you mean?",
        options=[
            {"label": "John Smith (john.smith@example.com)", "value": "john.smith@example.com"},
            {"label": "John Doe (john.doe@company.com)", "value": "john.doe@company.com"},
            {"label": "Johnny Appleseed (johnny@apple.com)", "value": "johnny@apple.com"},
        ]
    )
    time.sleep(5)

    # Hide HUD
    print("Hiding HUD...")
    server.hide()

    print()
    print("All tests complete!")
    print("Press Ctrl+C to exit...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        print("\nDone.")


if __name__ == "__main__":
    main()
