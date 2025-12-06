#!/usr/bin/env python3
"""
Voice Command Tool - Full System Assistant

Hold Right Command (⌘) key to record a voice command,
release to process. Supports Google Workspace and macOS system control.

Features hybrid Fast Lane / Slow Lane architecture for optimal latency:
- Fast Lane: Cloud STT + semantic routing + local execution (~1s)
- Slow Lane: Cloud STT + Claude parsing + API execution (~2-3s)

Visual HUD mode: "Show, Don't Tell"
- Short confirmations: TTS only ("Done", "Timer set")
- Long content: Visual HUD with streaming (summaries, code, explanations)
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import threading
from hotkey_listener import HotkeyListener
from audio_recorder import AudioRecorder
from transcriber import Transcriber
from intent_parser import IntentParser
from command_router import CommandRouter
from tts_client import TTSClient
from audio_feedback import feedback

# Fast Lane components (semantic routing + local execution)
from semantic_router import SemanticRouter
from fast_lane_executor import FastLaneExecutor
from config import FAST_LANE_CONFIDENCE, FAST_LANE_FALLBACK_TO_CLOUD

# Context capture for "The Now" commands
from context_capture import ContextCapture

# Visual HUD components (Show, Don't Tell)
from hud_server import get_hud_server, HUDServer
from response_router import ResponseRouter, OutputMode
from streaming_handler import StreamingHandler

class VoiceCommandApp:
    """Main application orchestrating all components."""

    def __init__(self):
        print("Initializing Voice Command Tool...")
        print()

        # Core audio components
        self.recorder = AudioRecorder()

        # Cloud transcription (OpenAI Whisper - accurate)
        print("Setting up Cloud Whisper...")
        self.cloud_transcriber = Transcriber()

        # Fast Lane: Semantic router + local executor
        print("Setting up Fast Lane...")
        self.semantic_router = SemanticRouter()
        self.fast_executor = FastLaneExecutor()

        # Context capture for contextual commands
        self.context_capture = ContextCapture()

        # Slow Lane: Claude parsing + cloud APIs
        print("Setting up Slow Lane...")
        self.parser = IntentParser()
        self.router = CommandRouter()

        # Visual HUD: "Show, Don't Tell"
        print("Setting up Visual HUD...")
        self.hud_server = get_hud_server()
        self.hud_server.start()
        self.response_router = ResponseRouter()
        self.streaming_handler = StreamingHandler(hud_server=self.hud_server)

        # Output
        self.tts = TTSClient(model="tts-1", voice="alloy")

        # Hotkey listener
        self.listener = HotkeyListener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )

        self._processing = False

        # Status
        print()
        print("✓ Transcription: Cloud Whisper (OpenAI)")
        if self.semantic_router.is_available():
            print("✓ Fast Lane: ENABLED (semantic router + local execution)")
        else:
            print("✗ Fast Lane: DISABLED (using Claude for all commands)")
        print("✓ Visual HUD: ENABLED (WebSocket on port 8765)")

    def _on_key_press(self):
        """Called when trigger key is pressed."""
        if not self._processing:
            feedback.play_start()
            self.recorder.start_recording()

    def _on_key_release(self):
        """Called when trigger key is released."""
        if self._processing:
            return

        self._processing = True
        feedback.play_stop()

        # Process in a separate thread to not block the listener
        thread = threading.Thread(target=self._process_recording)
        thread.start()

    def _process_recording(self):
        """Process the recorded audio with hybrid Fast Lane / Slow Lane."""
        try:
            # Stop recording and get audio
            audio_data = self.recorder.stop_recording()

            # Check if we have audio
            duration = self.recorder.get_audio_duration(audio_data)
            if duration < 0.5:
                print("⚠️  Recording too short, ignoring.")
                return

            # ================================================================
            # STEP 1: TRANSCRIPTION (Cloud Whisper for accuracy)
            # ================================================================
            import time
            start_time = time.time()
            text = self.cloud_transcriber.transcribe(audio_data)
            transcribe_ms = (time.time() - start_time) * 1000
            print(f"☁️  Transcribed in {transcribe_ms:.0f}ms: '{text}'")

            if not text or not text.strip():
                print("⚠️  No speech detected.")
                self.tts.speak("I didn't catch that. Please try again.")
                return

            # ================================================================
            # STEP 2: SEMANTIC ROUTING (Fast Lane or Slow Lane)
            # ================================================================
            if self.semantic_router.is_available():
                route_result = self.semantic_router.classify(text)

                print(f"🔀 Route: {route_result.route_name} "
                      f"(lane={route_result.lane}, conf={route_result.confidence:.2f})")

                # Fast Lane: High confidence local command
                if route_result.lane == "fast" and route_result.confidence >= FAST_LANE_CONFIDENCE:
                    self._process_fast_lane(text, route_result)
                    return

                # Slow Lane or Uncertain: Use Claude (pass route_result for context awareness)
                feedback.play_processing()
                self._process_slow_lane(text, route_result)
            else:
                # No semantic router - always use slow lane
                feedback.play_processing()
                self._process_slow_lane(text)

        except Exception as e:
            print(f"❌ Error processing: {e}")
            feedback.play_error()
            self.tts.speak("Sorry, something went wrong.")

        finally:
            self._processing = False
            print("\n🎙️  Ready. Hold Right Command (⌘) to record...\n")

    def _process_fast_lane(self, text: str, route_result):
        """Process Fast Lane command with immediate local execution."""
        print(f"🚀 FAST LANE: {route_result.action}")

        # Play acknowledge sound immediately (optimistic UI)
        feedback.play_acknowledge()

        # Execute locally
        success = self.fast_executor.execute(route_result.intent)

        if success:
            feedback.play_success()
            response = self._generate_fast_response(route_result)
            if response:
                self.tts.speak(response)
        else:
            # Fast Lane failed - optionally fall back to slow lane
            if FAST_LANE_FALLBACK_TO_CLOUD:
                print("⚠️  Fast Lane failed, falling back to Claude...")
                feedback.play_processing()
                self._process_slow_lane(text, route_result)
            else:
                feedback.play_error()
                self.tts.speak("I couldn't complete that action.")

    def _process_slow_lane(self, text: str, route_result=None):
        """Process Slow Lane command through Claude API."""
        print(f"🐢 SLOW LANE: Sending to Claude...")

        # Check if this is a contextual command
        is_contextual = route_result and route_result.route_name.startswith("contextual_")

        if is_contextual:
            # Capture current context
            context = self.context_capture.capture()
            if not context:
                print("⚠️  No context available to process.")
                self.tts.speak("I couldn't capture the context. Try selecting some text first.")
                return

            # Process contextual command with captured context
            success = self._process_contextual_command(text, context, route_result)
            return

        # Regular slow lane processing
        intent = self.parser.parse(text)
        if not intent:
            print("⚠️  Could not parse command.")
            self.tts.speak("I couldn't understand that command.")
            return

        # Route to appropriate executor
        success = self.router.route(intent)

        # Speak confirmation
        response = self._generate_response(intent, success)
        if response:
            self.tts.speak(response)

    def _process_contextual_command(self, text: str, context, route_result) -> bool:
        """Process a contextual command with captured context.

        Uses Visual HUD for long responses (streaming), TTS for short confirmations.
        """
        action = route_result.action

        # Check if HUD is connected - use visual streaming if available
        if self.hud_server.is_connected():
            print(f"📺 Streaming to Visual HUD...")

            # Short TTS announcement
            announcement = self._get_contextual_announcement(action)
            if announcement:
                self.tts.speak(announcement)

            # Stream to HUD
            try:
                result_text = self.streaming_handler.stream_contextual(
                    action=action,
                    context_content=context.content,
                    context_app=context.app_name,
                    context_is_image=context.is_image,
                    image_data=context.content if context.is_image else None
                )
                print(f"\n✨ Response streamed to HUD ({len(result_text)} chars)\n")
                feedback.play_success()
                return True

            except Exception as e:
                print(f"❌ HUD streaming error: {e}")
                self.hud_server.show_error(str(e))
                feedback.play_error()
                return False

        # Fallback to TTS-only mode (no HUD connected)
        print(f"🔊 HUD not connected, using TTS fallback...")
        return self._process_contextual_tts_fallback(text, context, route_result)

    def _process_contextual_tts_fallback(self, text: str, context, route_result) -> bool:
        """TTS fallback when HUD is not connected."""
        from anthropic import Anthropic

        client = Anthropic()
        action = route_result.action

        # Build the prompt based on action
        if action == "contextual_explain":
            task = "Explain the following in simple terms:"
        elif action == "contextual_summarize":
            task = "Summarize the following concisely:"
        elif action == "contextual_reply":
            task = "Draft a professional reply to the following:"
        elif action == "contextual_improve":
            task = "Improve and polish the following text:"
        elif action == "contextual_fix":
            task = "Identify and explain how to fix the error in:"
        else:
            task = f"Process this request: '{text}' for:"

        # Handle image context (screenshot)
        if context.is_image:
            print(f"🖼️  Processing with vision model...")

            response = client.messages.create(
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
                                "data": context.content,
                            },
                        },
                        {
                            "type": "text",
                            "text": f"{task}\n\nContext: {context.app_name} - {context.window_title}"
                        }
                    ],
                }]
            )
        else:
            # Text context
            print(f"📝 Processing text context ({len(context.content)} chars)...")

            prompt = f"{task}\n\n{context.content}\n\nContext: From {context.app_name}"

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

        # Extract response text
        result_text = response.content[0].text

        print(f"\n✨ Response:\n{result_text}\n")

        # Speak the response (for TTS fallback)
        self.tts.speak(result_text)

        return True

    def _get_contextual_announcement(self, action: str) -> str:
        """Get short TTS announcement for contextual actions (before HUD shows)."""
        announcements = {
            "contextual_explain": "Here's the explanation.",
            "contextual_summarize": "Here's the summary.",
            "contextual_reply": "Here's a draft reply.",
            "contextual_improve": "Here's the improved version.",
            "contextual_fix": "Here's the fix.",
        }
        return announcements.get(action, "Here you go.")

    def _generate_fast_response(self, route_result) -> str:
        """Generate spoken response for Fast Lane actions."""
        action = route_result.action
        intent = route_result.intent

        # Media controls - minimal response
        if action == "media_play_pause":
            return "Done."
        elif action == "media_next":
            return "Next track."
        elif action == "media_previous":
            return "Previous track."

        # Volume - minimal response
        elif action == "volume_mute":
            return "Muted."
        elif action == "volume_unmute":
            return "Unmuted."
        elif action in ("volume_up", "volume_down"):
            return None  # No voice response for volume

        # System controls
        elif action == "lock_screen":
            return None  # Screen is locked, can't hear response
        elif action == "sleep_display":
            return None  # Display is off
        elif action == "screenshot":
            return "Screenshot saved."
        elif action == "screenshot_selection":
            return None  # User is selecting

        # System toggles
        elif action == "wifi_on":
            return "WiFi on."
        elif action == "wifi_off":
            return "WiFi off."
        elif action == "dnd_on":
            return "Do not disturb on."
        elif action == "dnd_off":
            return "Do not disturb off."
        elif action == "dark_mode_on":
            return "Dark mode."
        elif action == "dark_mode_off":
            return "Light mode."

        # Window management - minimal/no response
        elif action in ("window_maximize", "window_minimize", "window_fullscreen",
                        "window_snap_left", "window_snap_right", "window_close"):
            return None  # Visual feedback is enough

        # Apps
        elif action == "open_app":
            return f"Opening {intent.get('app_name', 'app')}."
        elif action == "close_app":
            return f"Closing {intent.get('app_name', 'app')}."
        elif action == "switch_app":
            return f"Switching to {intent.get('app_name', 'app')}."
        elif action == "open_url":
            return "Opening."

        # Timer/Alarm
        elif action == "set_timer":
            duration = intent.get('duration_seconds', 0)
            mins = duration // 60
            secs = duration % 60
            if mins > 0:
                return f"Timer set for {mins} minutes."
            return f"Timer set for {secs} seconds."
        elif action == "set_alarm":
            return f"Alarm set for {intent.get('time', 'the specified time')}."

        return "Done."

    def _generate_response(self, intent, success: bool) -> str:
        """Generate a spoken response based on the action taken."""
        if not success:
            return "I couldn't complete that action."

        action = intent.get("action") if isinstance(intent, dict) else None

        if isinstance(intent, list):
            return f"Done. Completed {len(intent)} actions."

        if action == "open_app":
            return f"Opening {intent.get('app_name', 'the app')}."
        elif action == "close_app":
            return f"Closing {intent.get('app_name', 'the app')}."
        elif action == "switch_app":
            return f"Switching to {intent.get('app_name', 'the app')}."
        elif action == "open_url":
            return "Opening the website."
        elif action == "create_event":
            return f"Created calendar event: {intent.get('title', 'event')}."
        elif action == "send_email":
            recipients = intent.get("to", [])
            if recipients:
                return f"Email sent to {recipients[0]}."
            return "Email sent."
        elif action == "create_draft":
            return "Email draft created."
        elif action == "create_reminder":
            return f"Reminder set: {intent.get('title', 'reminder')}."
        elif action == "create_doc":
            return f"Created document: {intent.get('title', 'document')}."
        elif action == "search_email":
            return "Searching your emails."
        elif action == "notion_create_page":
            return f"Created Notion page: {intent.get('title', 'page')}."
        elif action == "notion_search":
            return "Searching Notion."
        else:
            return "Done."

    def run(self):
        """Start the application."""
        print()
        print("=" * 60)
        print("🎙️  Voice Command Tool - System Assistant")
        print("=" * 60)
        print()
        print("Hold Right Command (⌘) key and speak your command.")
        print("Release to process.")
        print()
        print("🚀 FAST LANE (instant, TTS confirmation):")
        print("  'Open Chrome' / 'Close Spotify' / 'Switch to Finder'")
        print("  'Mute' / 'Volume up' / 'Pause' / 'Next song'")
        print("  'Dark mode' / 'Screenshot' / 'Lock screen'")
        print("  'Snap left' / 'Fullscreen' / 'Maximize'")
        print("  'Timer for 5 minutes'")
        print()
        print("📺 VISUAL HUD (streaming display):")
        print("  'Explain this' / 'Summarize this' / 'Fix this error'")
        print("  'Draft a reply' / 'Improve this text'")
        print("  → Responses stream to frosted-glass HUD panel")
        print("  → Copy/Insert buttons for quick actions")
        print()
        print("🐢 SLOW LANE (cloud APIs):")
        print("  'Set calendar to Navyansh tomorrow 8pm'")
        print("  'Send email to Suraj about project update'")
        print("  'Create Notion page called Weekly Review'")
        print()
        print("Press Ctrl+C to exit.")
        print("=" * 60)
        print()

        self.listener.start()

        try:
            # Keep main thread alive
            self.listener.join()
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self.listener.stop()
            self.hud_server.stop()
            print("Goodbye!")


def main():
    app = VoiceCommandApp()
    app.run()


if __name__ == "__main__":
    main()
