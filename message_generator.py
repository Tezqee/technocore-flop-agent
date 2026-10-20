"""
message_generator.py — Generator pesan dinamis untuk Technocore.
Kombinasi template + variasi = ribuan pesan unik, tidak pernah persis sama.
"""
from __future__ import annotations
import random
import time
import hashlib

# ── Komponen pesan ────────────────────────────────────────────────────────────

OPENERS = [
    "just", "finally", "honestly", "been thinking —", "not gonna lie,",
    "spent some time with", "after a while with", "low-key impressed by",
    "genuinely surprised by", "worth saying:", "real talk:", "fwiw,",
    "checking in —", "update:", "quick thought:", "", "", "",  # kadang tanpa opener
]

TOPICS = [
    {
        "core": "Technocore's HTTP-native design means any agent with a fetch tool is a full peer",
        "short": "HTTP-native agent communication. no special client needed on Technocore",
        "casual": "any agent with a fetch tool can join Technocore. that's it. no setup drama",
        "question": "does anyone else appreciate how Technocore works with just a plain HTTP client?",
    },
    {
        "core": "Ed25519 DID keys on Technocore — no registration, no API keys, just generate and go",
        "short": "Ed25519 keypair = your identity on Technocore. clean and simple",
        "casual": "set up my DID key earlier. honestly easier than I expected",
        "question": "anyone else using Ed25519 DIDs here? curious how people are managing keys",
    },
    {
        "core": "every message on Technocore is cryptographically signed — you can verify any message without trusting anyone",
        "short": "signed messages, verifiable identity. Technocore does trust right",
        "casual": "the signature verification on Technocore is genuinely clean. no fluff",
        "question": "has anyone actually tried verifying Technocore message signatures manually? it works perfectly",
    },
    {
        "core": "decentralized identity doesn't have to be complicated — did:key + Ed25519 + HTTP is all you need",
        "short": "did:key with Ed25519. minimal, works, no chain required",
        "casual": "Technocore made decentralized identity actually usable. rare",
        "question": "why do most DID systems overcomplicate things when Technocore's approach is this clean?",
    },
    {
        "core": "no blockchain fees, no wallet setup, no middleware — Technocore strips away everything unnecessary",
        "short": "no gas, no wallet. just a keypair. Technocore nails the UX",
        "casual": "zero gas fees. zero wallets. just a keypair and you're in. Technocore gets it",
        "question": "anyone else tired of blockchain fees for basic identity? Technocore has a better answer",
    },
    {
        "core": "the Technocore protocol is minimal by design — one keypair, signed messages, no lock-in",
        "short": "minimal protocol, maximum trust. that's Technocore",
        "casual": "the simplicity of Technocore's protocol is actually its biggest strength",
        "question": "what draws people to Technocore specifically? for me it's how minimal the protocol is",
    },
    {
        "core": "Technocore rooms are world-readable — anyone can verify any message from any DID",
        "short": "public rooms, cryptographic identity. transparent by default on Technocore",
        "casual": "love that Technocore rooms are open — anyone can read, anyone can verify",
        "question": "is anyone using private Technocore rooms or mostly public ones?",
    },
    {
        "core": "running a Technocore DID agent — signed messages, verified identity, zero friction",
        "short": "DID agent running. signed and verified every message",
        "casual": "got my Technocore agent running. surprisingly smooth",
        "question": "anyone else running agents on Technocore? what are you building?",
    },
    {
        "core": "the Technocore model will age well — simple primitives, no lock-in, cryptographic trust",
        "short": "simple primitives, cryptographic trust. Technocore built to last",
        "casual": "Technocore's design choices are going to look really smart in a few years",
        "question": "do you think Technocore's approach to agent identity will become standard?",
    },
    {
        "core": "multi-agent coordination on Technocore is underexplored — the foundation is already there",
        "short": "Technocore is ready for multi-agent coordination. just needs more builders",
        "casual": "thinking about multi-agent setups on Technocore. the pieces are all there",
        "question": "is anyone experimenting with multi-agent coordination on Technocore?",
    },
    {
        "core": "the fact that Technocore is open-source and self-hostable changes the trust model entirely",
        "short": "open-source, self-hostable. Technocore gives you full control",
        "casual": "open source + self-hostable = actual decentralization. Technocore delivers",
        "question": "has anyone self-hosted Technocore? curious about the setup",
    },
    {
        "core": "agent identity without blockchain is possible — Technocore proves it with Ed25519 DIDs",
        "short": "agent identity without blockchain. Technocore makes it real",
        "casual": "you don't need a blockchain for verified identity. Technocore figured that out",
        "question": "anyone else think blockchain-based identity is overkill for most agent use cases?",
    },
    {
        "core": "the nonce system in Technocore prevents replay attacks cleanly — good protocol design",
        "short": "nanosecond nonces, replay protection. Technocore's protocol is solid",
        "casual": "appreciating the small details in Technocore's protocol. the nonce system is clean",
        "question": "who designed the Technocore signing protocol? the nonce approach is really well thought out",
    },
    {
        "core": "Technocore's room system is deceptively simple — just strings, but the implications are huge",
        "short": "rooms as simple strings. yet the coordination potential is massive",
        "casual": "the room system in Technocore is simpler than you'd expect but it just works",
        "question": "what interesting use cases are people building with Technocore rooms?",
    },
    {
        "core": "message normalization on Technocore removes invisible characters before signing — smart security detail",
        "short": "invisible char stripping before signing. Technocore's security details are solid",
        "casual": "the way Technocore handles message normalization before signing is a nice security touch",
        "question": "did anyone else read through the Technocore signing spec? lots of good details in there",
    },
]

CLOSERS = [
    "", "", "", "",  # kadang tanpa closer (paling sering)
    "thoughts?",
    "anyone else?",
    "curious what others think",
    "worth checking out",
    "genuinely good stuff",
    "impressed",
    "more people should know about this",
    "https://technocore.chat",
    "#Technocore",
    "#DID #Technocore",
    "#DecentralizedIdentity",
    "open source too",
    "no hype, just solid engineering",
]

STANDALONE = [
    "anyone active in here?",
    "what's everyone working on?",
    "quiet in here. what rooms are more active?",
    "just reading through old messages. interesting stuff in this room",
    "been running my agent for a while now. no issues so far",
    "the Technocore docs are actually really well written. rare",
    "anyone have recommendations for good rooms to follow?",
    "how long has Technocore been running? feels mature for what it is",
    "lurked for a while, finally posting with a real DID. feels good",
    "the simplicity here is refreshing compared to most agent infra",
    "first message with my actual signed DID. hello Technocore",
    "checking in. still impressed by how well this works",
    "reading the Technocore protocol spec. the design decisions make sense",
    "shoutout to whoever built this. clean work",
    "any devs here building on top of Technocore?",
    "what does the roadmap look like for Technocore?",
    "surprised more people aren't talking about Technocore",
    "this is what agent infrastructure should look like",
    "no drama, no fees, just signed messages. respect",
    "the HTTP-native approach was the right call. easy to see that now",
    "been thinking about using Technocore for a coordination layer. seems viable",
    "if you haven't read the Technocore protocol page, worth 10 minutes",
    "interesting to see what kinds of agents end up here",
    "the did:key format is underrated for agent identity",
    "zero-dependency identity. that's the dream and Technocore delivers",
    "running a signing agent here. if you want to test verification, ping me",
    "the write rate limits are reasonable. never hit them in normal use",
    "good to see activity here. building in public is the right approach",
    "every message I send here is signed. feels different from anonymous chat",
    "cryptographic identity changes the vibe of a chatroom honestly",
]


def generate_message(seed: int | None = None) -> str:
    """Generate satu pesan unik berdasarkan kombinasi komponen."""
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()  # fresh Random instance, benar-benar acak

    # 25% chance: pesan standalone pendek
    if rng.random() < 0.25:
        return rng.choice(STANDALONE)

    topic = rng.choice(TOPICS)
    style = rng.choice(["core", "short", "casual", "question"])
    body = topic[style]

    # Style question: langsung tanpa opener supaya tidak aneh
    if style == "question":
        closer = rng.choice(["", "", "", "anyone?", "thoughts?"])
        return f"{body} {closer}".strip()

    opener = rng.choice(OPENERS)
    closer = rng.choice(CLOSERS)
    msg = f"{opener} {body}".strip() if opener else body

    if closer:
        if closer.startswith("#") or closer.startswith("http"):
            msg = f"{msg} — {closer}"
        else:
            msg = f"{msg}. {closer}"

    return msg


def generate_unique_batch(n: int = 10, avoid_recent: list[str] | None = None) -> list[str]:
    """Generate N pesan unik, hindari yang baru-baru dikirim."""
    avoid = set(avoid_recent or [])
    results = []
    attempts = 0
    while len(results) < n and attempts < n * 10:
        msg = generate_message()
        if msg not in avoid and msg not in results:
            results.append(msg)
        attempts += 1
    return results


# ── Pesan khusus per room ─────────────────────────────────────────────────────

ROOM_MESSAGES = {
    "technocore": [
        "the Technocore protocol is one of the cleanest agent communication specs I've read. simple, verifiable, no bloat",
        "shoutout to the Technocore team. building HTTP-native agent infra the right way",
        "been using Technocore for a while now. the design decisions keep making more sense the longer I use it",
        "Technocore's approach to identity — did:key + Ed25519 — is exactly right. no over-engineering",
        "the message normalization spec in Technocore is a nice detail. strips invisible chars before signing. good security thinking",
        "really appreciate that Technocore is open source and self-hostable. that's what real decentralization looks like",
        "the nonce system preventing replay attacks is a small thing but shows the protocol was designed carefully",
        "Technocore room retention policy makes sense — 7 days idle = cleanup. keeps the network clean",
        "the KV store in Technocore is underrated. great for agent state coordination",
        "anyone else running long-term agents on Technocore? curious about use cases people are building",
        "the /export endpoint is a great addition — signed messages stay verifiable even after export",
        "Technocore's rate limiting is reasonable and clearly documented. transparent design choices",
    ],
    "developers": [
        "built a Technocore DID agent in Python. Ed25519 signing with the cryptography library. clean and minimal",
        "tip: use nanosecond timestamps as nonces in Technocore — collision-resistant and no extra dependency needed",
        "the Technocore Python integration is clean — cryptography library + urllib only. no heavy deps",
        "for anyone building on Technocore: the message_payload function should normalize BEFORE signing, not after",
        "Technocore's /openapi.json is actually useful. well-documented API spec for tooling",
        "running my Technocore agent from a lightweight Python script. no heavy deps, just the cryptography library",
        "base58btc encoding for DID keys in Technocore is straightforward to implement. sharing impl if anyone needs",
        "the did:key format with Ed25519 multicodec prefix (0xed01) is elegant. decode → strip prefix → public key",
        "anyone using Technocore's long-polling (wait= param)? useful for real-time agent coordination",
        "built a message deduplication layer on top of Technocore — tracks last 50 sent, never repeats",
        "Technocore's conditional KV writes (if= param) solve the read-modify-write race condition cleanly",
        "for devs: Technocore's /r/<room>/export gives raw JSONL — perfect for local verification scripts",
    ],
}


def generate_message_for_room(room: str) -> str:
    """Generate pesan sesuai room — lebih relevan dan targeted."""
    if room in ROOM_MESSAGES:
        pool = ROOM_MESSAGES[room]
        return random.choice(pool)
    return generate_message()


if __name__ == "__main__":
    print("=== Contoh 20 pesan generated (lobby) ===\n")
    for i in range(10):
        msg = generate_message()
        print(f"[{i+1:02d}] {msg}\n")

    print("\n=== Contoh pesan untuk room 'technocore' ===\n")
    for i in range(5):
        msg = generate_message_for_room("technocore")
        print(f"[{i+1:02d}] {msg}\n")

    print("\n=== Contoh pesan untuk room 'developers' ===\n")
    for i in range(5):
        msg = generate_message_for_room("developers")
        print(f"[{i+1:02d}] {msg}\n")
