#!/usr/bin/env python3
"""
Voice Command Tool - Full System Assistant

Hold Right Command (⌘) key to record a voice command,
release to process. Supports Google Workspace and macOS system control.

Features hybrid Fast Lane / Slow Lane architecture for optimal latency:
- Fast Lane: Local transcription + semantic routing + local execution (~350ms)
- Slow Lane: Cloud transcription + Claude parsing + API execution (~2-3s)
"""

import threading
from hotkey_listener import HotkeyListener
from audio_recorder import AudioRecorder
from transcriber import Transcriber
from intent_parser import IntentParser
from command_router import CommandRouter
from tts_client import TTSClient
from audio_feedback import feedback

# Local Fast Lane components
from local_transcriber import LocalTranscriber
from semantic_router import SemanticRouter
from fast_lane_executor import FastLaneExecutor
from config import LOCAL_WHISPER_MAX_DURATION, FAST_LANE_CONFIDENCE, FAST_LANE_FALLBACK_TO_CLOUD

class VoiceCommandApp:
    """Main application orchestrating all components."""

    def __init__(self):
        print("Initializing Voice Command Tool...")
        print()

        # Core audio components
        self.recorder = AudioRecorder()

        # Local Fast Lane components
        print("Setting up Local Fast Lane...")
        self.local_transcriber = LocalTranscriber()
        self.semantic_router = SemanticRouter()
        self.fast_executor = FastLaneExecutor()
        self._use_local = self.local_transcriber.is_available()

        # Cloud Slow Lane components (fallback)
        print("Setting up Cloud Slow Lane...")
        self.cloud_transcriber = Transcriber()
        self.parser = IntentParser()
        self.router = CommandRouter()

        # Output
        self.tts = TTSClient(model="tts-1", voice="alloy")

        # Hotkey listener
        self.listener = HotkeyListener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )

        self._processing = False

        # Status
        if self._use_local:
            print("✓ Local Fast Lane: ENABLED (whisper.cpp)")
        else:
            print("✗ Local Fast Lane: DISABLED (using cloud only)")

        if self.semantic_router.is_available():
            print("✓ Semantic Router: ENABLED (fastembed)")
        else:
            print("✗ Semantic Router: DISABLED (using Claude only)")

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
            # STEP 1: TRANSCRIPTION (Local or Cloud)
            # ================================================================
            text = None
            used_local = False

            # Try local transcription first for short commands
            if self._use_local and duration < LOCAL_WHISPER_MAX_DURATION:
                try:
                    result = self.local_transcriber.transcribe(audio_data)
                    if result.text and result.confidence > 0.5:
                        text = result.text
                        used_local = True
                        print(f"🚀 [Local] Transcribed in {result.latency_ms:.0f}ms: '{text}'")
                except Exception as e:
                    print(f"⚠️  Local transcription failed: {e}")

            # Fallback to cloud transcription
            if not text:
                text = self.cloud_transcriber.transcribe(audio_data)
                print(f"☁️  [Cloud] Transcribed: '{text}'")

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

                # Slow Lane or Uncertain: Use Claude
                feedback.play_processing()
                self._process_slow_lane(text)
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
                self._process_slow_lane(text)
            else:
                feedback.play_error()
                self.tts.speak("I couldn't complete that action.")

    def _process_slow_lane(self, text: str):
        """Process Slow Lane command through Claude API."""
        print(f"🐢 SLOW LANE: Sending to Claude...")

        # Parse intent with Claude
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
        print("Release to process. I'll speak the response back!")
        print()
        print("🚀 FAST LANE (instant, <400ms):")
        print("  'Open Chrome' / 'Close Spotify' / 'Switch to Finder'")
        print("  'Mute' / 'Volume up' / 'Pause' / 'Next song'")
        print("  'Dark mode' / 'Screenshot' / 'Lock screen'")
        print("  'Snap left' / 'Fullscreen' / 'Maximize'")
        print("  'Timer for 5 minutes'")
        print()
        print("🐢 SLOW LANE (cloud, ~2-3s):")
        print("  'Set calendar to Navyansh tomorrow 8pm'")
        print("  'Send email to Suraj about project update'")
        print("  'Remind me to call client at 3pm'")
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
            print("Goodbye!")


def main():
    app = VoiceCommandApp()
    app.run()


if __name__ == "__main__":
    main()
