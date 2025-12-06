# Voice Assistant Product Research: Signal vs Noise

## The Core Question
**What makes a voice assistant a PAINKILLER vs a VITAMIN?**

---

## Key Research Findings

### Why Current Voice Assistants FAIL

| Problem | Evidence |
|---------|----------|
| **95% frustration rate** | Only 5% never get frustrated with voice search |
| **Stuck in 2016** | "Siri feels like a voice assistant from 2016 living in 2025" |
| **Multi-step tasks fail** | Apple's Siri V1 reboot scrapped in early 2025 - "couldn't converge" |
| **Low actual usage** | 46% of US adults NEVER use voice assistants; only 16% use daily |
| **Boiled down to timers** | "Ask anyone how they use these - playing music or setting a timer" |
| **Trust issues** | 46% don't trust voice assistants for payments/orders |
| **Public awkwardness** | 74% only use voice assistants at home - "looks weird" in public |

**Root Cause**: "Voice assistants were never designed to serve user needs. The users aren't its customers—they're the product." - [The Register](https://www.theregister.com/2022/12/14/voice_assistants_failed/)

---

### The PAINKILLER Moments (When Voice is NEEDED, Not Wanted)

#### 1. **Hands-Full Situations** 🧑‍🍳
> "I feel like I shouldn't touch the phone, with my salmonella riddled hands."

- Cooking with raw meat
- Carrying groceries/baby
- Hands dirty (garage, gardening)
- Driving (safety-critical)

#### 2. **Accessibility** ♿
> For people with disabilities, "virtual assistants save valuable time—no more battling with screen readers."

- 50 million Americans over 65 today → 78 million by 2035
- Visual impairment, motor limitations, cognitive challenges
- **This is a NEED, not a want**
- BUT: Current assistants fail with non-standard accents/speech patterns

#### 3. **Multitasking Parents** 👨‍👩‍👧‍👦
> "AI voice calling to set routines for kids, remind them about homework, or read bedtime stories—all while taking care of other household tasks."

- Dictating grocery list while cooking dinner
- Setting reminders while managing kids
- Voice dictation in the car (school runs)
- 40% of time freed by effective delegation

#### 4. **Micro-Moments of Urgency**
- Quick timer while hands are busy
- "Remind me in 10 minutes" while doing something
- Sending a text while driving (legal in some places)

---

### What DOESN'T Work (VITAMIN Territory)

| Use Case | Why It Fails |
|----------|--------------|
| **Shopping/Commerce** | Trust issues, preference for visual browsing |
| **Complex research** | People switch to screen for anything non-trivial |
| **Conversation/Chat** | Nobody wants to talk to AI for fun (exception: lonely elderly) |
| **Multi-step workflows** | Error rate too high, "books incorrect dates" |
| **Public usage** | Social stigma, "looks weird" |

---

## The Key Insight: Utilitarian Consumer Thesis

From [Menlo Ventures 2025 State of Consumer AI](https://menlovc.com/perspective/2025-the-state-of-consumer-ai/):

> **"People adopt tools that help them do what they ALREADY NEED to do, but in a better, faster, cheaper way."**

- Most consumers stick with familiar general AI tools
- They test their preferred tool FIRST, only seek alternatives when it fails
- **Implication**: Don't build a "voice assistant" - build a **voice-activated action executor** for specific moments

---

## What Actually Drives Adoption

### Latency is EVERYTHING
> "500ms voice-to-voice response time is just barely possible with today's AI models" - [HN Discussion](https://news.ycombinator.com/item?id=40805010)

- GPT-4o's Advanced Voice Mode drove massive growth (near-human fluency)
- Multimodal + speed = magic

### Time Savings Data
| Metric | Impact |
|--------|--------|
| Meeting scheduling time | -30% with voice |
| Routine task delegation | Frees 40% of employee time |
| Professionals using digital organizers | 25% more likely to meet deadlines |
| 65% prefer voice-driven scheduling | Speed + no manual entry |

---

## Signal Over Noise: What to BUILD

### ✅ HIGH SIGNAL (Painkiller)
1. **Hands-busy action completion** - cooking, driving, carrying
2. **Ultra-fast task execution** - <3 second round-trip
3. **No conversation required** - action confirmation only
4. **Accessibility-first design** - works with various speech patterns
5. **Specific moment targeting** - don't be general-purpose

### ❌ LOW SIGNAL (Vitamin/Noise)
1. Conversational AI chat
2. General-purpose assistant
3. Commerce/shopping
4. Entertainment queries
5. Complex multi-step workflows

---

## The Consumer Behavior Change

### Before (Failed Model)
```
User → Speaks complex request → Assistant tries to understand → Fails → User gives up
```

### After (What Works)
```
User's hands are full → Simple voice trigger → ONE action completes → Done
```

**The shift**: From "voice assistant as conversational partner" to "voice as fastest input method when hands are occupied"

---

## Competitive Landscape Signal

| Product | What They Do | Traction Signal |
|---------|--------------|-----------------|
| **ChatGPT Voice Mode** | Conversation + actions | 400M weekly users (doubled in 6 months) |
| **OpenAI Operator** | Browser automation | $200/month Pro only, 38% benchmark |
| **Claude Computer Use** | Desktop + browser | 22% OSWorld benchmark, still buggy |
| **Home Assistant + LLM** | Smart home control | Strong DIY community adoption |

**Gap**: None focus purely on **ACTION COMPLETION + LOW LATENCY** for **HANDS-BUSY MOMENTS**

---

## Product Hypothesis

### The Wedge
**Target moment**: When hands are physically occupied but brain is free
- Cooking
- Driving (Android Auto/CarPlay)
- Working out
- Carrying things

### The Promise
> "Voice command → Action completed → Minimal confirmation"
> NOT: "Voice command → Conversation → Clarification → Maybe action"

### Success Metric
- **Action completion rate** (not conversation quality)
- **Time to action completion** (<3 seconds)
- **Retry rate** (should be near zero)

---

## FOCUSED DIRECTION: Desktop Power User + Latency Obsession

### User Decisions
- **Target**: Desktop power user (developers/knowledge workers)
- **Confirmation**: Sound cue only (beep for success, different beep for error)
- **Differentiation**: Latency obsession (3x faster than Siri)

### Latency Benchmarks (What's Possible)

| Component | Best-in-class | Notes |
|-----------|---------------|-------|
| **STT** | <300ms | Gladia real-time, GPT-4o transcribe |
| **Local STT** | ~100-200ms | Distil-Whisper (6x faster, 49% smaller) |
| **LLM** | 500-1500ms | Claude Haiku fastest, Sonnet for complex |
| **TTS** | ELIMINATED | Sound cue = ~50ms |
| **Total Target** | **<1.5 seconds** | vs Siri's 3-5+ seconds |

### Competitive Analysis: Desktop Voice Control

| Tool | Strength | Weakness |
|------|----------|----------|
| **macOS Voice Control** | Built-in, free | Clunky, not AI-powered |
| **VoiceAttack** | Gaming focus, customizable | Windows only, no AI |
| **Braina** | AI + voice + automation | Windows only |
| **Raycast** | Fast, dev-focused | No voice input |
| **Siri** | Integrated | Slow, limited, frustrating |

**Gap**: No **AI-powered, latency-obsessed, sound-only** voice action executor for Mac power users

### The Product Thesis

**For desktop power users**, your competitive advantage is:
1. **Speed** - <1.5s end-to-end (eliminate TTS entirely)
2. **Reliability** - action completes or clear error sound
3. **Minimal friction** - push-to-talk, no wake word
4. **OS-level depth** - control ANY app via AppleScript

**NOT competing on**:
- Conversation quality (don't need it)
- Voice quality (sound cues only)
- Complex multi-step workflows (keep it simple)

### Architecture for Latency

```
[Right Cmd Press] → [Start beep]
         ↓
[Local STT: Distil-Whisper] (~200ms)
         ↓
[Claude Haiku for intent] (~500ms)
         ↓
[AppleScript execution] (~100ms)
         ↓
[Success/Error beep] (~50ms)
         ↓
TOTAL: ~850ms - 1.2s
```

### Key Changes to Current Implementation

1. **Remove TTS entirely** - replace with sound cues
2. **Switch to local STT** - Distil-Whisper or faster-whisper
3. **Use Claude Haiku** for simple intent parsing (faster)
4. **Optimize AppleScript** - pre-compile common commands

---

## USER VALIDATION PLAN

### Where to Find Mac Power Users

| Community | Why | Size/Activity |
|-----------|-----|---------------|
| **r/MacApps** | Power users looking for productivity tools | Active subreddit |
| **Mac Power Users Forum** | Dedicated productivity enthusiasts | High-intent users |
| **HackerNews** | Developers, early adopters, builders | "Show HN" potential |
| **IndieHackers** | Makers who build productivity tools | Meta audience |
| **Apple Development Discord** | ~15K Mac developers | Technical users |
| **Raycast Discord** | Users already invested in Mac productivity | Perfect fit |
| **Twitter/X** | #buildinpublic, Mac productivity influencers | Distribution later |

### Interview Questions (Avoid Bias)

**Context Questions (Start Here):**
1. "Walk me through how you typically control your Mac throughout the day"
2. "What's the last thing you tried to do with Siri that didn't work?"
3. "When do you wish you didn't have to use your keyboard/mouse?"

**Pain Discovery:**
4. "Tell me about a time you were frustrated with how long something took on your Mac"
5. "What repetitive actions do you do 10+ times per day?"
6. "When do you find yourself saying 'I wish I could just...'"

**Current Behavior:**
7. "What tools do you use for automation? (Raycast, Alfred, Keyboard Maestro?)"
8. "Have you ever tried voice control on your Mac? What happened?"
9. "What made you stop using [voice tool they mentioned]?"

**Validation (NOT "Would you use this?"):**
10. "If this existed, what's the first thing you'd try to do with it?"
11. "Can you think of a scenario where this WOULDN'T work for you?"
12. "Would you be willing to try an early version and give feedback?"

### Red Flags to Listen For

| Red Flag | What It Means |
|----------|---------------|
| "That would be cool" | Vitamin, not painkiller |
| "I guess I could use that" | No real pain |
| "Siri does that already" | Not differentiated enough |
| "I prefer typing" | Wrong target user |

### Green Lights to Listen For

| Green Light | What It Means |
|-------------|---------------|
| "I've literally wanted this for years" | Real pain |
| "I'd pay for that" | Willingness to pay |
| "Can I get early access?" | High intent |
| "I tried X but it was too slow/unreliable" | Competitor weakness |

### Minimum Users to Talk To
- **5 users** to identify main problems (Jakob Nielsen rule)
- **15 total** across 3 sessions to validate
- **Target**: Developers who use Mac 8+ hours/day

### Outreach Template

> "Hey [name], I'm building a voice-controlled action executor for Mac power users - optimized for speed (<1.5s), not conversation.
>
> I noticed you [use Raycast / post about Mac productivity / etc].
>
> Would you be open to a 15-min chat about your workflow? Trying to understand if this is a real pain point or just a nice-to-have.
>
> No pitch, just learning."

---

## Sources

- [HN: Why are voice assistants still buggy in 2024?](https://news.ycombinator.com/item?id=40026576)
- [Why Siri Still Struggles in 2025](https://www.landofgeek.com/posts/why-siri-still-bad-apple-ai)
- [Menlo Ventures: 2025 State of Consumer AI](https://menlovc.com/perspective/2025-the-state-of-consumer-ai/)
- [Voice Assistants Failed - The Register](https://www.theregister.com/2022/12/14/voice_assistants_failed/)
- [IBM: AI Agents 2025 Expectations vs Reality](https://www.ibm.com/think/insights/ai-agents-2025-expectations-vs-reality)
- [Accessibility & Voice Assistants - Wiley](https://onlinelibrary.wiley.com/doi/10.1155/2024/6494944)
- [Voice-to-Text for Busy Parents](https://productivityparents.com/the-power-of-voice-to-text-tools-for-busy-parents/)
- [HN: 500ms Voice Bot Response Times](https://news.ycombinator.com/item?id=40805010)
- [Attest: 2025 Consumer AI Adoption Report](https://www.askattest.com/blog/articles/2025-consumer-adoption-of-ai-report)

---

*Research compiled: December 2024*
