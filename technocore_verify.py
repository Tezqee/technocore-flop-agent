#!/usr/bin/env python3
"""
technocore_verify.py – Offline signature verifier for Technocore messages.

Usage:
    python technocore_verify.py \\
        --did  "did:key:z6Mk..." \\
        --room "lobby" \\
        --nonce "1234567890" \\
        --text "Hello from Technocore!" \\
        --sig  "base64url-86-char-signature"

Exit codes:
    0 – signature is valid
    1 – signature is invalid or inputs are malformed
"""

from __future__ import annotations

import argparse
import sys

# Reuse the protocol helpers from the original agent
# (the agent must be in the same directory)
try:
    from technocore_agent import (
        ProtocolError,
        IdentityError,
        message_payload,
        verify_bytes,
    )
except ImportError:
    sys.exit(
        "Could not import technocore_agent.\n"
        "Make sure technocore_verify.py is in the same folder as technocore_agent.py."
    )


def verify(did: str, room: str, nonce: str, text: str, signature: str) -> bool:
    """Return True if the Ed25519 signature is valid for this message."""
    try:
        _, payload = message_payload(room, nonce, text)
        verify_bytes(did, signature, payload)
        return True
    except (ProtocolError, IdentityError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a Technocore Ed25519 message signature offline."
    )
    parser.add_argument("--did",   required=True, help="did:key:z6Mk… identity")
    parser.add_argument("--room",  required=True, help="Technocore room name")
    parser.add_argument("--nonce", required=True, help="Server-assigned nonce")
    parser.add_argument("--text",  required=True, help="Original message text")
    parser.add_argument("--sig",   required=True, help="86-char base64url signature")

    args = parser.parse_args()

    ok = verify(
        did=args.did,
        room=args.room,
        nonce=args.nonce,
        text=args.text,
        signature=args.sig,
    )

    if ok:
        print("✅ VALID – signature matches DID and payload.")
        return 0
    else:
        print("❌ INVALID – signature check failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
