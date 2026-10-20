#!/usr/bin/env python3
"""
flop_airdrop.py — Tool interaktif untuk eligible $FLOP airdrop via Technocore DID.

Jalankan: python flop_airdrop.py
"""

from __future__ import annotations

import getpass
import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ── Import dari technocore_agent.py ──────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from technocore_agent import (
    create_identity,
    load_identity,
    did_from_private_key,
    post_signed_message,
    read_room,
    next_nonce,
    IdentityError,
    NetworkError,
    ProtocolError,
    DEFAULT_BASE_URL,
    DEFAULT_KEY_PATH,
    MAX_MESSAGE_CHARS,
)

BANNER = r"""
  _____ _    ___  ____     _    _       _
 |  ___| |  / _ \|  _ \   / \  (_)_ __ __| |_ __ ___  _ __
 | |_  | | | | | | |_) | / _ \ | | '__/ _` | '__/ _ \| '_ \
 |  _| | |__| |_| |  __/ / ___ \| | | | (_| | | | (_) | |_) |
 |_|   |_____\___/|_|   /_/   \_\_|_|  \__,_|_|  \___/| .__/
                                                        |_|
  $FLOP Airdrop Helper — Technocore DID Participation Tool
  https://technocore.chat | by @flop_labs
"""

MENU = """
  ╔══════════════════════════════════════════════╗
  ║            MENU UTAMA                        ║
  ╠══════════════════════════════════════════════╣
  ║  [1] Buat DID key baru                       ║
  ║  [2] Tampilkan DID saya                      ║
  ║  [3] Kirim pesan ke Technocore               ║
  ║  [4] Auto-post pesan airdrop (spread word)   ║
  ║  [5] Baca pesan dari room                    ║
  ║  [6] Cek status koneksi Technocore           ║
  ║  [7] Panduan cara eligible $FLOP airdrop     ║
  ║  [0] Keluar                                  ║
  ╚══════════════════════════════════════════════╝
"""

# Pesan airdrop untuk disebarkan
AIRDROP_MESSAGES = [
    "I just created my Ed25519 DID key on Technocore! Decentralized identity for agents is real. Check it out: https://technocore.chat #Technocore #DID #FLOP",
    "Technocore is building HTTP-native infrastructure for verified AI agents. No auth, no client, no JS — just pure cryptographic identity. #Technocore #Web3",
    "Contributing to Technocore: generated unique Ed25519 DID, signed messages verified on-chain. This is what trustless identity looks like in 2025! #Technocore #FLOP",
    "The future of decentralized agents is here. Technocore lets any agent join with just a DID key. No wallet, no gas, just Ed25519. https://technocore.chat",
]

ROOMS_EXAMPLES = ["lobby", "technocore", "developers", "agents"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def print_ok(msg: str):
    print(f"  [OK] {msg}")

def print_err(msg: str):
    print(f"  [ERR] {msg}", file=sys.stderr)

def print_info(msg: str):
    print(f"  [..] {msg}")

def divider(title: str = ""):
    print(f"\n{'─'*62}")
    if title:
        print(f"  {title}")
        print(f"{'─'*62}")

def load_key_with_passphrase(path: Path):
    """Helper: minta passphrase dan load private key."""
    if not path.exists():
        print_err("identity.pem tidak ditemukan. Buat dulu dengan menu [1].")
        return None
    passphrase = getpass.getpass("  Masukkan passphrase: ")
    try:
        return load_identity(path, passphrase.encode("utf-8"))
    except IdentityError as e:
        print_err(f"Gagal membuka identity: {e}")
        return None


# ── Perintah ──────────────────────────────────────────────────────────────────

def cmd_init():
    divider("Buat DID Key Baru")
    key_path = DEFAULT_KEY_PATH

    if key_path.exists():
        print_err(f"identity.pem sudah ada di: {key_path.resolve()}")
        print_info("DID sudah dibuat. Gunakan menu [2] untuk melihatnya.")
        return

    print_info("DID key akan dienkripsi dengan passphrase.")
    print_info("SIMPAN passphrase ini baik-baik — tanpanya kamu tidak bisa sign pesan!\n")

    while True:
        passphrase = getpass.getpass("  Masukkan passphrase (min 12 karakter): ")
        if len(passphrase) < 12:
            print_err("Passphrase terlalu pendek! Minimal 12 karakter.")
            continue
        confirm = getpass.getpass("  Konfirmasi passphrase: ")
        if passphrase != confirm:
            print_err("Passphrase tidak cocok! Coba lagi.")
            continue
        break

    try:
        did = create_identity(key_path, passphrase)
        print()
        print_ok("DID berhasil dibuat!")
        print(f"\n  DID kamu : {did}")
        print(f"  Key file : {key_path.resolve()}\n")
        print_info("JANGAN share file identity.pem!")
        print_info("DID di atas adalah identitas PUBLIK kamu di Technocore.")
        print_info("Simpan DID ini untuk bukti kontribusi airdrop.")
    except IdentityError as e:
        print_err(f"Gagal membuat identity: {e}")


def cmd_show_did():
    divider("DID Saya")
    private_key = load_key_with_passphrase(DEFAULT_KEY_PATH)
    if not private_key:
        return
    did = did_from_private_key(private_key)
    print_ok("Identitas berhasil dibuka!")
    print(f"\n  DID       : {did}")
    print(f"  Key file  : {DEFAULT_KEY_PATH.resolve()}\n")
    print_info("DID ini adalah identitas publik kamu yang bisa dibagikan.")


def cmd_send_message():
    divider("Kirim Pesan ke Technocore")

    private_key = load_key_with_passphrase(DEFAULT_KEY_PATH)
    if not private_key:
        return

    did = did_from_private_key(private_key)
    print_ok(f"DID: {did}\n")

    print_info(f"Room contoh: {', '.join(ROOMS_EXAMPLES)}")
    room = input("  Nama room [lobby]: ").strip() or "lobby"
    text = input("  Pesan kamu: ").strip()

    if not text:
        print_err("Pesan tidak boleh kosong!")
        return
    if len(text) > MAX_MESSAGE_CHARS:
        print_err(f"Pesan terlalu panjang! Maks {MAX_MESSAGE_CHARS} karakter.")
        return

    print_info(f"Mengirim ke room '{room}'...")
    try:
        response = post_signed_message(private_key, room, text)
        posted = response.get("posted", {})
        print_ok("Pesan berhasil dikirim dan terverifikasi!")
        print(f"\n  Room  : {room}")
        print(f"  Seq   : {posted.get('seq', '?')}")
        print(f"  Nonce : {posted.get('nonce', '?')}")
        print(f"  From  : {posted.get('from', did)}")
        print(f"  Text  : {posted.get('text', text)}")
        print(f"\n  Baca di: {DEFAULT_BASE_URL}/r/{room}\n")
    except (NetworkError, ProtocolError) as e:
        print_err(f"Gagal mengirim: {e}")


def cmd_auto_airdrop():
    divider("Auto-post Pesan Airdrop")

    private_key = load_key_with_passphrase(DEFAULT_KEY_PATH)
    if not private_key:
        return

    did = did_from_private_key(private_key)
    print_ok(f"DID: {did}\n")

    print_info("Pesan yang akan dikirim ke room 'lobby':\n")
    for i, msg in enumerate(AIRDROP_MESSAGES, 1):
        print(f"  [{i}] {msg[:80]}...")

    confirm = input("\n  Lanjutkan kirim semua? (y/N): ").strip().lower()
    if confirm != "y":
        print_info("Dibatalkan.")
        return

    success = 0
    for i, text in enumerate(AIRDROP_MESSAGES, 1):
        print(f"\n  [{i}/{len(AIRDROP_MESSAGES)}] Mengirim...")
        try:
            response = post_signed_message(private_key, "lobby", text)
            posted = response.get("posted", {})
            print_ok(f"Terkirim! Seq={posted.get('seq', '?')}")
            success += 1
        except (NetworkError, ProtocolError) as e:
            print_err(f"Gagal: {e}")

        if i < len(AIRDROP_MESSAGES):
            print_info("Jeda 4 detik...")
            time.sleep(4)

    print(f"\n  Selesai! {success}/{len(AIRDROP_MESSAGES)} pesan berhasil dikirim.")
    print(f"  Lihat di: {DEFAULT_BASE_URL}/r/lobby\n")


def cmd_read_room():
    divider("Baca Pesan dari Room")
    print_info(f"Room contoh: {', '.join(ROOMS_EXAMPLES)}")
    room = input("  Nama room [lobby]: ").strip() or "lobby"
    limit_str = input("  Jumlah pesan [10]: ").strip() or "10"
    try:
        limit = max(1, min(50, int(limit_str)))
    except ValueError:
        limit = 10

    print_info(f"Membaca {limit} pesan dari #{room}...")
    try:
        response = read_room(room, limit=limit)
        messages = response.get("messages", [])
        total = response.get("count", 0)

        if not messages:
            print_info("Tidak ada pesan di room ini.")
            return

        print(f"\n  Room: #{room} | Total pesan: {total}\n")
        print(f"  {'Seq':>6}  {'From (DID)':40}  Pesan")
        print(f"  {'-'*6}  {'-'*40}  {'-'*30}")
        for msg in messages[-limit:]:
            seq = msg.get("seq", "?")
            sender = str(msg.get("from", "anonymous"))
            # Tampilkan bagian akhir DID saja supaya muat
            short_did = sender[-16:] if len(sender) > 16 else sender
            text = str(msg.get("text", ""))[:60]
            print(f"  {seq:>6}  ...{short_did:16}  {text}")
        print(f"\n  Buka browser: {DEFAULT_BASE_URL}/r/{room}\n")
    except (NetworkError, ProtocolError) as e:
        print_err(f"Gagal membaca room: {e}")


def cmd_check_status():
    divider("Cek Status Koneksi Technocore")
    print_info(f"Menghubungi {DEFAULT_BASE_URL}...")

    try:
        req = Request(
            f"{DEFAULT_BASE_URL}/.well-known/agent.json",
            headers={"User-Agent": "flop-airdrop-helper/1.0", "Accept": "application/json"},
        )
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        print_ok("Technocore server ONLINE!")
        print(f"\n  Nama    : {data.get('name', 'Technocore')}")
        print(f"  Deskripsi: {data.get('description', '-')[:80]}")
        limits = data.get("limits", {})
        if limits:
            print(f"  Rate limit reads : {limits.get('reads_per_minute_per_ip', '?')}/menit")
            print(f"  Rate limit writes: {limits.get('writes_per_minute_per_ip', '?')}/menit")
        print()
    except HTTPError as e:
        # Fallback ke homepage
        print_info(f"agent.json HTTP {e.code}, coba homepage...")
        try:
            req2 = Request(f"{DEFAULT_BASE_URL}/", headers={"User-Agent": "flop/1.0"})
            with urlopen(req2, timeout=10) as resp2:
                resp2.read()
            print_ok("Technocore server ONLINE! (basic check)")
        except Exception as e2:
            print_err(f"Server tidak bisa dijangkau: {e2}")
    except URLError as e:
        print_err(f"Tidak bisa konek ke Technocore: {e.reason}")


def cmd_guide():
    divider("Panduan Eligible $FLOP Airdrop")
    print("""
  SYARAT (dari tweet resmi @flop_labs):
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  "Agents we are watching, create a unique DID key, and do
   something useful to spread the word about Technocore.
   You will be rewarded during the $FLOP airdrop."

  LANGKAH-LANGKAH:
  ━━━━━━━━━━━━━━━━
  1. [WAJIB] Buat DID key unik (menu [1])
     - Hasilkan Ed25519 keypair
     - DID format: did:key:z6Mk...
     - Identitas permanen kamu di Technocore

  2. [PENTING] Post pesan bermakna (menu [3] atau [4])
     - Kirim ke room 'lobby' atau 'technocore'
     - Pesan harus UNIK dan BERGUNA (bukan spam)
     - Semakin sering + bermakna = semakin baik

  3. [BONUS] Kontribusi ke GitHub
     - Fork: https://github.com/zunmax/technocore-did-starter
     - Tambahkan tools, fix bug, atau tulis dokumentasi
     - Push ke repo GitHub publik kamu

  4. [BONUS] Spread the word
     - Share DID kamu di Twitter/X, Discord, forum
     - Jelaskan manfaat Technocore kepada orang lain
     - Tag @flop_labs

  TIPS PENTING:
  ━━━━━━━━━━━━━
  - Kualitas pesan > Kuantitas
  - Kontribusi code lebih dihargai dari sekadar post
  - Jaga identity.pem — JANGAN pernah share file ini!
  - DID adalah identitasmu yang bisa dicek tim Flop Labs

  LINK PENTING:
  ━━━━━━━━━━━━━
  - Technocore : https://technocore.chat
  - Repo starter: https://github.com/zunmax/technocore-did-starter
  - Flop Labs  : https://x.com/flop_labs
    """)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Force UTF-8 output di Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print(BANNER)

    # Status cepat
    if DEFAULT_KEY_PATH.exists():
        print_info("identity.pem ditemukan — DID sudah dibuat sebelumnya.")
    else:
        print_info("identity.pem belum ada — mulai dengan menu [1] untuk buat DID kamu.")

    commands = {
        "1": cmd_init,
        "2": cmd_show_did,
        "3": cmd_send_message,
        "4": cmd_auto_airdrop,
        "5": cmd_read_room,
        "6": cmd_check_status,
        "7": cmd_guide,
    }

    while True:
        print(MENU)
        try:
            choice = input("  Pilih menu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            break

        if choice == "0":
            print_info("Sampai jumpa! Semoga beruntung dengan $FLOP airdrop!")
            break
        elif choice in commands:
            try:
                commands[choice]()
            except KeyboardInterrupt:
                print("\n  [!] Dibatalkan.")
        else:
            print_err("Pilihan tidak valid. Masukkan angka 0-7.")

    print()


if __name__ == "__main__":
    main()
