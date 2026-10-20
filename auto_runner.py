#!/usr/bin/env python3
"""
auto_runner.py — Jalankan otomatis: post pesan ke Technocore secara berkala.

Setup sekali:
    set TECHNOCORE_PASS=passphrase_kamu  (Windows CMD)
    $env:TECHNOCORE_PASS="passphrase_kamu"  (PowerShell)

Lalu jalankan:
    python auto_runner.py
    python auto_runner.py --interval 300   # kirim tiap 5 menit
    python auto_runner.py --once           # kirim sekali lalu keluar
    python auto_runner.py --room technocore --interval 600
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import json
import random
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from technocore_agent import (
    load_identity,
    did_from_private_key,
    post_signed_message,
    read_room,
    IdentityError,
    NetworkError,
    ProtocolError,
    DEFAULT_KEY_PATH,
    DEFAULT_BASE_URL,
)
from message_generator import generate_message, generate_message_for_room

# ── Konfigurasi default ───────────────────────────────────────────────────────
DEFAULT_INTERVAL   = 600          # detik antar pesan (10 menit)
DEFAULT_ROOM       = "lobby"
LOG_FILE           = Path("auto_runner.log")

# ── Rotasi pesan ──────────────────────────────────────────────────────────────
# ── Rotasi pesan ──────────────────────────────────────────────────────────────
# Pesan di-generate dinamis oleh message_generator.py
# Kombinasi template + variasi = ribuan kemungkinan, tidak pernah persis sama
RECENT_MESSAGES_FILE = Path("recent_messages.json")
MAX_RECENT = 50  # hindari 50 pesan terakhir


def get_next_message(room: str = "lobby") -> str:
    """Generate pesan baru sesuai room, hindari yang baru-baru dikirim."""
    recent: list[str] = []
    if RECENT_MESSAGES_FILE.exists():
        try:
            recent = json.loads(RECENT_MESSAGES_FILE.read_text(encoding="utf-8"))
        except Exception:
            recent = []

    avoid = set(recent[-MAX_RECENT:])
    for _ in range(30):
        msg = generate_message_for_room(room)
        if msg not in avoid:
            break

    recent.append(msg)
    if len(recent) > MAX_RECENT:
        recent = recent[-MAX_RECENT:]
    try:
        RECENT_MESSAGES_FILE.write_text(
            json.dumps(recent, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass

    return msg


# ── Logger ────────────────────────────────────────────────────────────────────
def log(level: str, msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def log_info(msg: str):  log("INFO ", msg)
def log_ok(msg: str):    log("OK   ", msg)
def log_err(msg: str):   log("ERROR", msg)
def log_warn(msg: str):  log("WARN ", msg)


# ── Load passphrase ───────────────────────────────────────────────────────────
def get_passphrase() -> bytes:
    """Ambil passphrase dari env var TECHNOCORE_PASS."""
    passphrase = os.environ.get("TECHNOCORE_PASS", "").strip()
    if not passphrase:
        log_err("Environment variable TECHNOCORE_PASS tidak diset!")
        log_err("Jalankan dulu:")
        log_err('  PowerShell : $env:TECHNOCORE_PASS="passphrase_kamu"')
        log_err('  CMD        : set TECHNOCORE_PASS=passphrase_kamu')
        sys.exit(1)
    return passphrase.encode("utf-8")


# ── Post satu pesan ───────────────────────────────────────────────────────────
def post_one(private_key, did: str, room: str, text: str) -> bool:
    """Post pesan ke Technocore. Return True jika berhasil."""
    try:
        response = post_signed_message(private_key, room, text)
        posted = response.get("posted", {})
        seq = posted.get("seq", "?")
        log_ok(f"Terkirim ke #{room} | seq={seq} | {text[:60]}...")
        return True
    except NetworkError as e:
        log_err(f"Network error: {e}")
        return False
    except ProtocolError as e:
        log_err(f"Protocol error: {e}")
        return False


# ── Mode: jalankan sekali ─────────────────────────────────────────────────────
def run_once(private_key, did: str, room: str):
    log_info(f"Mode: sekali | DID: {did}")
    msg = get_next_message(room)
    success = post_one(private_key, did, room, msg)
    if success:
        log_ok("Selesai!")
    else:
        log_err("Gagal mengirim pesan.")
        sys.exit(1)


# ── Mode: loop otomatis ───────────────────────────────────────────────────────
def run_loop(private_key, did: str, room: str, interval: int, max_posts: int):
    log_info(f"Mode: otomatis | Room: #{room} | Interval: ~{interval}s (random +-20%) | Max: {'tak terbatas' if max_posts == 0 else max_posts}")
    log_info(f"DID: {did}")
    log_info(f"Log tersimpan di: {LOG_FILE.resolve()}")
    log_info("Pesan di-generate dinamis — tidak akan persis sama!")
    log_info("Tekan Ctrl+C untuk berhenti.\n")

    count = 0

    while True:
        # Jeda random sebelum post (terasa lebih manusiawi)
        pre_delay = random.randint(5, 45)
        log_info(f"Bersiap... (jeda {pre_delay}s)")
        time.sleep(pre_delay)

        # Generate pesan baru sesuai room
        msg = get_next_message(room)

        success = post_one(private_key, did, room, msg)
        if success:
            count += 1

        # Cek batas maksimum
        if max_posts > 0 and count >= max_posts:
            log_ok(f"Sudah kirim {count} pesan. Berhenti.")
            break

        # Interval random +-20% dari target supaya tidak tepat jam
        variance = int(interval * 0.2)
        actual_wait = interval + random.randint(-variance, variance)
        log_info(f"Pesan ke-{count} terkirim. Menunggu {actual_wait}s sebelum pesan berikutnya...")
        try:
            time.sleep(actual_wait)
        except KeyboardInterrupt:
            log_info("Dihentikan oleh user.")
            break


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Force UTF-8 di Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Auto-post pesan Technocore untuk eligible $FLOP airdrop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python auto_runner.py                        # loop tiap 10 menit
  python auto_runner.py --once                 # kirim sekali lalu keluar
  python auto_runner.py --interval 300         # tiap 5 menit
  python auto_runner.py --room technocore      # ke room technocore
  python auto_runner.py --max-posts 10         # kirim max 10 pesan
  python auto_runner.py --interval 3600 --room lobby  # tiap 1 jam

Passphrase (wajib set dulu):
  PowerShell: $env:TECHNOCORE_PASS="passphrase_kamu"
  CMD:        set TECHNOCORE_PASS=passphrase_kamu
        """
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Kirim satu pesan lalu keluar"
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_INTERVAL, metavar="DETIK",
        help=f"Jeda antar pesan dalam detik (default: {DEFAULT_INTERVAL})"
    )
    parser.add_argument(
        "--room", default=DEFAULT_ROOM,
        help=f"Nama room tujuan (default: {DEFAULT_ROOM})"
    )
    parser.add_argument(
        "--max-posts", type=int, default=0, metavar="N",
        help="Batas maksimum pesan yang dikirim (0 = tak terbatas)"
    )
    parser.add_argument(
        "--key", default=str(DEFAULT_KEY_PATH), metavar="PATH",
        help=f"Path ke identity.pem (default: {DEFAULT_KEY_PATH})"
    )
    args = parser.parse_args()

    print("=" * 62)
    print("  Technocore Auto Runner — $FLOP Airdrop Helper")
    print("=" * 62)

    # Validasi interval minimum
    if args.interval < 10:
        log_warn("Interval minimum 10 detik. Diset ke 10 detik.")
        args.interval = 10

    # Load passphrase
    passphrase = get_passphrase()

    # Load identity
    key_path = Path(args.key)
    if not key_path.exists():
        log_err(f"identity.pem tidak ditemukan di: {key_path.resolve()}")
        log_err("Buat DID dulu dengan: python flop_airdrop.py → menu [1]")
        sys.exit(1)

    log_info(f"Membuka identity dari: {key_path.resolve()}")
    try:
        private_key = load_identity(key_path, passphrase)
        did = did_from_private_key(private_key)
        log_ok(f"Identity berhasil dibuka!")
        log_ok(f"DID: {did}")
    except IdentityError as e:
        log_err(f"Gagal buka identity: {e}")
        log_err("Cek passphrase di TECHNOCORE_PASS sudah benar.")
        sys.exit(1)

    print()

    # Jalankan
    try:
        if args.once:
            run_once(private_key, did, args.room)
        else:
            run_loop(private_key, did, args.room, args.interval, args.max_posts)
    except KeyboardInterrupt:
        log_info("Dihentikan.")

    print()


if __name__ == "__main__":
    main()
