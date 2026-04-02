# 21-4

## Problem

Problem: When Claude AI runs as a subprocess inside the game engine, its internal telemetry is invisible — we can't see what it's doing, how long it takes, or where it fails. Why it matters: Without this visibility, the GM dashboard is blind to AI activity. Debugging production issues requires guesswork, and we can't prove the AI is actually engaging game mechanics versus improvising.

---

## What Changed

Think of it like adding a tracking chip to a delivery driver. Previously, when we sent Claude out to narrate a game scene, it left the building and we had no idea what happened until it came back with a result. Now, when Claude launches, we hand it a set of configuration cards that tell it "report your activity to our monitoring system." Claude reads those cards, does its work, and our dashboard lights up with real-time data about exactly what it did.

Technically: the `ClaudeClientBuilder` (the factory that creates Claude subprocess jobs) gained a new `.otel_endpoint()` configuration option. When that's set, every Claude subprocess inherits seven environment variables that wire it into our OpenTelemetry monitoring pipeline. When it's not set, nothing changes — clean fallback, no noise.

---

## Why This Approach

Environment variables are the standard contract between a host process and its subprocesses. We don't need to modify Claude's code, patch its binary, or build a custom IPC channel. We just speak the language it already understands. This is the same pattern used by every major cloud observability platform — AWS X-Ray, Datadog, Honeycomb all work this way.

The alternative (intercepting Claude's output and parsing telemetry from stdout) would be fragile, format-dependent, and would break every time Claude's output format changed. Env vars are a stable, version-independent contract.

Gating on `otel_endpoint: None` ensures zero overhead in environments where monitoring isn't configured — local dev stays clean.

---
