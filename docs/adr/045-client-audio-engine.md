# ADR-045: Client Audio Engine

> Retrospective — documents a decision already implemented in the codebase.

## Status
Accepted

## Context
The game client plays three concurrent audio streams: background music (cinematic, pre-rendered .ogg files), sound effects, and TTS voice narration (raw PCM s16le delivered as binary WebSocket frames). These streams must mix, duck, and sequence correctly: music drops during narration, voice segments queue sequentially even when they arrive faster than playback, and the whole system must respect browser autoplay policy (AudioContext requires a user gesture before it will produce sound).

HTML5 `<audio>` elements can't mix channels or accept raw PCM. Third-party libraries like Howler.js don't handle raw PCM without a decode step that fails on headerless PCM data. The audio system needed to be built directly on the Web Audio API.

## Decision
A singleton `AudioEngine` owns a three-channel Web Audio graph: music → sfx → voice, each channel with an independent gain node feeding a master gain node feeding the destination. Two auxiliary modules handle cross-cutting concerns.

`Crossfader` manages music transitions: when a new track is requested, it overlaps the fade-out of the current track with the fade-in of the new one, avoiding the silence gap of a sequential stop/start.

`Ducker` listens for TTS start/end events and ramps music gain down to 50% over 200ms when voice begins, then restores over 500ms when voice ends. The asymmetric ramp (fast duck, slow restore) matches broadcast audio ducking conventions.

TTS segments arrive as binary WebSocket frames (raw PCM s16le). A `voiceChain` Promise queue serializes playback — each segment appends to the tail of the chain, guaranteeing sequential playback even when segments arrive out of order or faster than real-time.

```typescript
// Raw PCM playback — decodeAudioData cannot handle headerless PCM
async playVoicePCM(pcmBuffer: ArrayBuffer): Promise<void> {
  const samples = new Int16Array(pcmBuffer);
  const audioBuffer = this.ctx.createBuffer(1, samples.length, SAMPLE_RATE);
  const channelData = audioBuffer.getChannelData(0);
  for (let i = 0; i < samples.length; i++) {
    channelData[i] = samples[i] / 32768.0; // normalize s16le to [-1, 1]
  }
  // ... connect to voice gain node and play
}
```

The AudioContext is created inside the first user gesture handler (browser requirement). A visibility change listener resumes the context when the tab regains focus after backgrounding. Volume state persists to localStorage.

Implemented in `sidequest-ui/src/audio/AudioEngine.ts`, `Ducker.ts`, `Crossfader.ts`.

## Alternatives Considered

- **HTML5 Audio elements** — No mixing control, no programmatic gain, no channel routing. Cannot duck music under voice without platform-specific hacks.
- **Howler.js** — Mature library but doesn't handle raw PCM. Would require a WAV header wrapper around every TTS frame, adding per-frame complexity.
- **MediaSource API** — Designed for streaming video/audio with known container formats. Overkill for raw PCM of known format and sample rate; adds MSE buffer management complexity.

## Consequences

**Positive:**
- Full mixing control: music, sfx, and voice are independently gained and routable.
- `Ducker` produces broadcast-quality narration clarity without player intervention.
- `voiceChain` queue handles backpressure — rapid TTS segments play cleanly without overlap or drops.
- No library dependency for core audio functionality.

**Negative:**
- Raw PCM normalization loop runs on the main thread for each TTS segment — should move to an AudioWorklet for large buffers.
- AudioContext autoplay gate requires careful initialization sequencing; errors surface only at runtime in new browser versions.
- Three-channel graph is hand-wired — adding a fourth channel (e.g., ambient) requires manual graph surgery.
- Volume persistence in localStorage is lost in private browsing mode.
