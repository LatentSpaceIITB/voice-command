"""Semantic Router for fast local intent classification.

Uses sentence embeddings (fastembed) to classify voice commands into
Fast Lane or Slow Lane routes based on semantic similarity.
"""

import json
import numpy as np
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from config import (
    ROUTES_CONFIG_FILE,
    EMBEDDING_MODEL,
    FAST_LANE_CONFIDENCE,
    SLOW_LANE_CONFIDENCE,
)
from intent_extractor import intent_extractor


@dataclass
class RouteResult:
    """Result from semantic routing."""
    route_name: str  # Name of the matched route (e.g., "media_play_pause")
    lane: str  # "fast", "slow", or "uncertain"
    confidence: float  # Similarity score (0-1)
    action: str  # Action to execute (e.g., "media_play_pause")
    intent: dict  # Full intent dict with extracted parameters


class SemanticRouter:
    """Fast intent classification using sentence embeddings."""

    def __init__(self):
        """Initialize the semantic router with fastembed model."""
        self.routes = {}
        self.route_embeddings = {}
        self.embedding_model = None
        self._available = False

        self._load_routes()
        self._initialize_embeddings()

    def _load_routes(self):
        """Load route definitions from config file."""
        config_path = Path(ROUTES_CONFIG_FILE)
        if not config_path.exists():
            print(f"Warning: Routes config not found at {config_path}")
            return

        with open(config_path, "r") as f:
            config = json.load(f)

        self.routes = config.get("routes", {})
        self.thresholds = config.get("thresholds", {
            "fast_lane": FAST_LANE_CONFIDENCE,
            "slow_lane": SLOW_LANE_CONFIDENCE,
        })

        print(f"Loaded {len(self.routes)} routes from config")

    def _initialize_embeddings(self):
        """Initialize fastembed model and precompute route embeddings."""
        try:
            from fastembed import TextEmbedding

            print(f"Loading embedding model: {EMBEDDING_MODEL}...")
            self.embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)

            # Precompute embeddings for all route utterances
            print("Precomputing route embeddings...")
            for route_name, route_config in self.routes.items():
                utterances = route_config.get("utterances", [])
                if utterances:
                    # Get embeddings for all utterances
                    embeddings = list(self.embedding_model.embed(utterances))
                    # Store as numpy array for fast similarity computation
                    self.route_embeddings[route_name] = np.array(embeddings)

            self._available = True
            print(f"Semantic router ready with {len(self.route_embeddings)} routes")

        except ImportError:
            print("Warning: fastembed not installed. Run: pip install fastembed")
            self._available = False
        except Exception as e:
            print(f"Warning: Failed to initialize semantic router: {e}")
            self._available = False

    def is_available(self) -> bool:
        """Check if the semantic router is available."""
        return self._available

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def _find_best_route(self, text: str) -> tuple[str, float]:
        """Find the best matching route for the given text.

        Returns:
            Tuple of (route_name, confidence_score)
        """
        if not self._available or not self.route_embeddings:
            return ("unknown", 0.0)

        # Get embedding for input text
        text_embedding = list(self.embedding_model.embed([text]))[0]

        best_route = "unknown"
        best_score = 0.0

        # Compare against all route embeddings
        for route_name, route_embeds in self.route_embeddings.items():
            # Compute similarity with each utterance embedding
            similarities = []
            for embed in route_embeds:
                sim = self._cosine_similarity(text_embedding, embed)
                similarities.append(sim)

            # Use max similarity (best match among utterances)
            max_sim = max(similarities) if similarities else 0.0

            if max_sim > best_score:
                best_score = max_sim
                best_route = route_name

        return (best_route, best_score)

    def classify(self, text: str) -> RouteResult:
        """Classify input text into a route.

        Args:
            text: Transcribed voice command

        Returns:
            RouteResult with route info, lane, confidence, and extracted intent
        """
        # Find best matching route
        route_name, confidence = self._find_best_route(text)

        # Get route config
        route_config = self.routes.get(route_name, {})
        lane = route_config.get("lane", "slow")
        action = route_config.get("action", route_name)

        # Determine effective lane based on confidence
        if lane == "fast" and confidence >= self.thresholds["fast_lane"]:
            effective_lane = "fast"
        elif confidence >= self.thresholds["slow_lane"]:
            effective_lane = lane
        else:
            effective_lane = "uncertain"

        # Extract parameters using intent extractor
        intent = intent_extractor.extract_for_action(action, text)

        return RouteResult(
            route_name=route_name,
            lane=effective_lane,
            confidence=confidence,
            action=action,
            intent=intent,
        )

    def get_lane(self, text: str) -> tuple[str, float]:
        """Quick lane determination without full intent extraction.

        Returns:
            Tuple of (lane, confidence)
        """
        result = self.classify(text)
        return (result.lane, result.confidence)


# Global instance
semantic_router = SemanticRouter()


if __name__ == "__main__":
    import time

    print("\nTesting Semantic Router")
    print("=" * 50)

    router = SemanticRouter()

    if not router.is_available():
        print("Semantic router not available. Install fastembed:")
        print("  pip install fastembed")
        exit(1)

    # Test cases
    test_commands = [
        # Fast Lane - Media
        "play music",
        "pause",
        "next song",
        "skip",
        "volume up",
        "mute",

        # Fast Lane - System
        "lock screen",
        "take screenshot",
        "dark mode",

        # Fast Lane - Apps
        "open chrome",
        "close spotify",
        "switch to finder",

        # Fast Lane - Windows
        "snap left",
        "maximize window",
        "fullscreen",

        # Fast Lane - Timer
        "timer for 5 minutes",

        # Slow Lane - Calendar
        "set meeting with John tomorrow",
        "create calendar event",

        # Slow Lane - Email
        "send email to Suraj",
        "draft email about project",

        # Slow Lane - Notion
        "create notion page",
        "search notion",

        # Uncertain
        "do something random",
        "help me with stuff",
    ]

    print("\nClassification Results:")
    print("-" * 70)
    print(f"{'Command':<35} {'Route':<20} {'Lane':<10} {'Conf':>6}")
    print("-" * 70)

    total_time = 0
    for cmd in test_commands:
        start = time.time()
        result = router.classify(cmd)
        elapsed = (time.time() - start) * 1000
        total_time += elapsed

        lane_emoji = {
            "fast": "🚀",
            "slow": "🐢",
            "uncertain": "❓"
        }.get(result.lane, "")

        print(f"{cmd:<35} {result.route_name:<20} {lane_emoji} {result.lane:<8} {result.confidence:.3f}")

    print("-" * 70)
    avg_time = total_time / len(test_commands)
    print(f"\nAverage classification time: {avg_time:.1f}ms")

    # Show detailed result for one command
    print("\n\nDetailed result for 'open chrome':")
    result = router.classify("open chrome")
    print(f"  Route: {result.route_name}")
    print(f"  Lane: {result.lane}")
    print(f"  Confidence: {result.confidence:.3f}")
    print(f"  Action: {result.action}")
    print(f"  Intent: {result.intent}")
