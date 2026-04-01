#!/usr/bin/env python3
"""Generate a complete NPC identity from genre pack data.

Produces a full NPC block (name, pronouns, role, appearance, personality)
from culture naming patterns, archetype templates, and OCEAN profiles.
The narrator calls this when introducing a new NPC instead of improvising.

Usage:
    python scripts/generate_npc.py --genre mutant_wasteland --culture Scrapborn
    python scripts/generate_npc.py --genre mutant_wasteland --archetype "Wasteland Trader"
    python scripts/generate_npc.py --genre mutant_wasteland --culture Scrapborn --gender female
    python scripts/generate_npc.py --genre mutant_wasteland --culture Scrapborn --role mechanic --description "old, missing an eye"

Output (JSON):
    {
      "name": "Thenvara Copperjaw",
      "pronouns": "she/her",
      "culture": "Scrapborn",
      "archetype": "Wasteland Trader",
      "role": "trader",
      "appearance": "Weathered woman with copper wire woven through her hair...",
      "personality": "shrewd, cheerfully cynical, knows everyone's business",
      "ocean_summary": "outgoing and talkative, pragmatic, emotionally steady",
      "disposition": 10
    }
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

# Markov chain — ported from sidequest-genre/src/markov.rs
START = "^"
END = "$"


class MarkovChain:
    def __init__(self, lookback: int = 2):
        self.lookback = lookback
        self.chain: dict[str, dict[str, int]] = {}
        self.reject_words: set[str] = set()

    def add_word(self, word: str) -> None:
        lower = word.lower().strip()
        if not lower:
            return
        key = list(START * self.lookback)
        for ch in lower:
            ctx = "".join(key)
            self.chain.setdefault(ctx, {})
            self.chain[ctx][ch] = self.chain[ctx].get(ch, 0) + 1
            key.pop(0)
            key.append(ch)
        ctx = "".join(key)
        self.chain.setdefault(ctx, {})
        self.chain[ctx][END] = self.chain[ctx].get(END, 0) + 1

    def train_file(self, text: str) -> None:
        """Train on raw text — strips Gutenberg headers, splits into words."""
        lines = text.splitlines()
        in_body = False
        body_lines = []
        for line in lines:
            if not in_body:
                if "*** START" in line:
                    in_body = True
                continue
            if "*** END" in line:
                break
            body_lines.append(line)
        corpus = "\n".join(body_lines) if body_lines else text
        for line in corpus.splitlines():
            for word in line.split():
                cleaned = "".join(ch for ch in word if ch.isalpha())
                if cleaned:
                    self.add_word(cleaned)

    def make_word(self) -> str:
        key = list(START * self.lookback)
        result = []
        for _ in range(20):
            ctx = "".join(key)
            options = self.chain.get(ctx, {})
            if not options:
                break
            total = sum(options.values())
            r = random.randint(1, total)
            cumulative = 0
            chosen = END
            for ch, count in options.items():
                cumulative += count
                if r <= cumulative:
                    chosen = ch
                    break
            if chosen == END:
                break
            result.append(chosen)
            key.pop(0)
            key.append(chosen)
        word = "".join(result)
        if word.lower() in self.reject_words:
            return self.make_word()  # retry
        return word

    def is_empty(self) -> bool:
        return len(self.chain) == 0


class SlotGenerator:
    def __init__(self, chain: MarkovChain | None, word_list: list[str]):
        self.chain = chain
        self.word_list = word_list

    def generate(self) -> str:
        has_chain = self.chain is not None and not self.chain.is_empty()
        has_list = bool(self.word_list)
        if not has_chain and not has_list:
            return ""
        use_chain = has_chain and (not has_list or random.random() < 0.67)
        if use_chain and self.chain:
            for _ in range(20):
                word = self.chain.make_word()
                if 2 <= len(word) <= 12:
                    return word
            return self.chain.make_word()
        if has_list:
            return random.choice(self.word_list)
        return ""


class NameGenerator:
    def __init__(self, slots: dict[str, SlotGenerator], person_patterns: list[str]):
        self.slots = slots
        self.person_patterns = person_patterns

    def generate_person(self) -> str:
        if not self.person_patterns:
            return ""
        pattern = random.choice(self.person_patterns)
        return self._fill(pattern)

    def _fill(self, pattern: str) -> str:
        cache: dict[str, str] = {}
        result = pattern
        while "{" in result and "}" in result:
            start = result.index("{")
            end = result.index("}")
            slot_name = result[start + 1 : end]
            if slot_name not in cache:
                gen = self.slots.get(slot_name)
                cache[slot_name] = gen.generate() if gen else slot_name
            result = result[:start] + cache[slot_name] + result[end + 1 :]
        return titlecase(result)


SMALL_WORDS = {"de", "of", "the", "and", "le", "la", "von", "van", "du", "des"}


def titlecase(name: str) -> str:
    words = name.split()
    result = []
    for i, w in enumerate(words):
        if i == 0 or w.lower() not in SMALL_WORDS:
            result.append(w[0].upper() + w[1:] if w else "")
        else:
            result.append(w.lower())
    return " ".join(result)


def load_yaml(path: Path) -> any:
    import yaml

    with open(path) as f:
        return yaml.safe_load(f)


def find_corpus_file(corpus_dir: Path, filename: str) -> Path | None:
    """Resolve corpus file, following symlinks and checking fallback locations."""
    direct = corpus_dir / filename
    if direct.exists():
        return direct
    # Resolve symlink target manually — symlinks may point to shared corpus
    if direct.is_symlink():
        target = direct.resolve()
        if target.exists():
            return target
    # Fallback: check orchestrator-level shared corpus
    root = Path(__file__).resolve().parent.parent
    shared = root / "corpus" / "shared" / filename
    if shared.exists():
        return shared
    return None


def build_generator(culture: dict, corpus_dir: Path) -> NameGenerator:
    slots: dict[str, SlotGenerator] = {}
    for slot_name, slot_config in culture.get("slots", {}).items():
        chain = None
        corpora = slot_config.get("corpora", [])
        if corpora:
            lookback = slot_config.get("lookback", 2)
            chain = MarkovChain(lookback)
            for corpus_ref in corpora:
                corpus_path = find_corpus_file(corpus_dir, corpus_ref["corpus"])
                if corpus_path:
                    rounds = max(1, round(corpus_ref.get("weight", 1.0)))
                    text = corpus_path.read_text()
                    for _ in range(rounds):
                        chain.train_file(text)
        word_list = slot_config.get("word_list", []) or []
        slots[slot_name] = SlotGenerator(chain if chain and not chain.is_empty() else None, word_list)
    return NameGenerator(slots, culture.get("person_patterns", []))


OCEAN_LABELS = {
    "openness": {
        "low": "conventional and practical",
        "mid": "balanced between tradition and novelty",
        "high": "curious and imaginative",
    },
    "conscientiousness": {
        "low": "spontaneous and flexible",
        "mid": "moderately organized",
        "high": "meticulous and disciplined",
    },
    "extraversion": {
        "low": "reserved and quiet",
        "mid": "selectively social",
        "high": "outgoing and talkative",
    },
    "agreeableness": {
        "low": "blunt and competitive",
        "mid": "pragmatic",
        "high": "warm and cooperative",
    },
    "neuroticism": {
        "low": "emotionally steady",
        "mid": "occasionally anxious",
        "high": "easily stressed and reactive",
    },
}


def ocean_summary(ocean: dict[str, float]) -> str:
    parts = []
    for dim, labels in OCEAN_LABELS.items():
        val = ocean.get(dim, 5.0)
        if val < 4.0:
            parts.append(labels["low"])
        elif val > 7.0:
            parts.append(labels["high"])
        else:
            parts.append(labels["mid"])
    return ", ".join(parts)


def jitter_ocean(base: dict[str, float], amount: float = 1.5) -> dict[str, float]:
    result = {}
    for dim, val in base.items():
        jittered = val + random.uniform(-amount, amount)
        result[dim] = max(0.0, min(10.0, round(jittered, 1)))
    return result


GENDER_PRONOUNS = {
    "male": "he/him",
    "female": "she/her",
    "nonbinary": "they/them",
}


def generate_npc(
    genre_dir: Path,
    culture_name: str | None = None,
    archetype_name: str | None = None,
    gender: str | None = None,
    role: str | None = None,
    description: str | None = None,
) -> dict:
    cultures = load_yaml(genre_dir / "cultures.yaml")
    archetypes = load_yaml(genre_dir / "archetypes.yaml")
    corpus_dir = genre_dir / "corpus"

    # Select culture
    culture = None
    if culture_name:
        culture = next((c for c in cultures if c["name"].lower() == culture_name.lower()), None)
    if not culture:
        culture = random.choice(cultures)

    # Select archetype
    archetype = None
    if archetype_name:
        archetype = next(
            (a for a in archetypes if a["name"].lower() == archetype_name.lower()), None
        )
    if not archetype:
        archetype = random.choice(archetypes)

    # Generate name (retry on degenerate results)
    gen = build_generator(culture, corpus_dir)
    name = ""
    for _ in range(10):
        candidate = gen.generate_person()
        # Reject names that start with small words (empty slot produced "Of the ...")
        if candidate and not candidate.lower().startswith(("of ", "the ", "and ")):
            name = candidate
            break
    if not name:
        name = gen.generate_person()  # last resort

    # Gender + pronouns
    if not gender:
        gender = random.choice(["male", "female", "nonbinary"])
    pronouns = GENDER_PRONOUNS.get(gender, "they/them")

    # OCEAN personality (jittered from archetype baseline)
    base_ocean = archetype.get("ocean", {
        "openness": 5.0, "conscientiousness": 5.0, "extraversion": 5.0,
        "agreeableness": 5.0, "neuroticism": 5.0,
    })
    ocean = jitter_ocean(base_ocean)

    # Role
    npc_role = role or archetype["name"].lower()

    # Personality traits
    traits = archetype.get("personality_traits", [])

    # Build result
    result = {
        "name": name,
        "pronouns": pronouns,
        "gender": gender,
        "culture": culture["name"],
        "archetype": archetype["name"],
        "role": npc_role,
        "personality": ", ".join(traits) if traits else "",
        "ocean": ocean,
        "ocean_summary": ocean_summary(ocean),
        "disposition": archetype.get("disposition_default", 0),
    }

    # Appearance from archetype description + user description
    appearance_parts = []
    if description:
        appearance_parts.append(description)
    if archetype.get("description"):
        appearance_parts.append(archetype["description"][:120])
    result["appearance"] = ". ".join(appearance_parts) if appearance_parts else ""

    # Dialogue quirks if available
    quirks = archetype.get("dialogue_quirks", [])
    if quirks:
        result["dialogue_quirks"] = quirks

    return result


def main():
    parser = argparse.ArgumentParser(description="Generate a complete NPC identity")
    parser.add_argument("--genre", required=True, help="Genre slug (e.g., mutant_wasteland)")
    parser.add_argument("--culture", help="Culture name (e.g., Scrapborn)")
    parser.add_argument("--archetype", help="Archetype name (e.g., 'Wasteland Trader')")
    parser.add_argument("--gender", choices=["male", "female", "nonbinary"])
    parser.add_argument("--role", help="NPC role override (e.g., mechanic)")
    parser.add_argument("--description", help="Physical description hints")
    parser.add_argument("--genre-packs-dir", type=Path, default=None,
                        help="Path to genre_packs/ directory")
    args = parser.parse_args()

    if args.genre_packs_dir:
        packs_dir = args.genre_packs_dir
    else:
        packs_dir = Path(__file__).resolve().parent.parent / "sidequest-content" / "genre_packs"

    genre_dir = packs_dir / args.genre
    if not genre_dir.is_dir():
        print(f"Error: genre pack not found at {genre_dir}", file=sys.stderr)
        sys.exit(1)

    npc = generate_npc(
        genre_dir,
        culture_name=args.culture,
        archetype_name=args.archetype,
        gender=args.gender,
        role=args.role,
        description=args.description,
    )
    print(json.dumps(npc, indent=2))


if __name__ == "__main__":
    main()
