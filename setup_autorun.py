#!/usr/bin/env python3
"""
setup_autorun.py — Setup sekali, jalan selamanya.
Simpan passphrase ke file lokal (terenkripsi base64) dan buat shortcut startup Windows.
"""
import base64
import os
import sys
import subprocess
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / ".tc_config"
STARTUP_FOLDER = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Startup"
SHORTCUT_NAME  = "TechnocoreAutoRunner.bat"
PROJECT_DIR    = Path(__file__).parent

def save_passphrase(passphrase: str):
    """Simpan passphrase ke file config (base64 encoded)."""
    encoded = base64.b64encode(passphrase.encode("utf-8")).decode()
    CONFIG_FILE.write_text(encoded, encoding="utf-8")
    print(f"  [OK] Passphrase tersimpan di: {CONFIG_FILE}")

def load_passphrase() -> str:
    """Load passphrase dari file config."""
    if not CONFIG_FILE.exists():
        return ""
    encoded = CONFIG_FILE.read_text(encoding="utf-8").strip()
    return base64.b64decode(encoded).decode("utf-8")

def create_startup_bat():
    """Buat file .bat di folder Startup Windows supaya jalan otomatis saat PC nyala."""
    bat_path = STARTUP_FOLDER / SHORTCUT_NAME
    python_exe = PROJECT_DIR / ".venv/Scripts/pythonw.exe"  # pythonw = tanpa jendela konsol
    runner_py  = PROJECT_DIR / "auto_runner.py"
    config_py  = PROJECT_DIR / "setup_autorun.py"

    bat_content = f"""@echo off
cd /d "{PROJECT_DIR}"
for /f "delims=" %%P in ('"{PROJECT_DIR}\\.venv\\Scripts\\python.exe" "{config_py}" --get-pass') do set TECHNOCORE_PASS=%%P
"{python_exe}" "{runner_py}" --interval 600 --room lobby
"""
    try:
        STARTUP_FOLDER.mkdir(parents=True, exist_ok=True)
        bat_path.write_text(bat_content, encoding="utf-8")
        print(f"  [OK] Startup shortcut dibuat: {bat_path}")
        return True
    except Exception as e:
        print(f"  [ERR] Gagal buat startup: {e}")
        return False

def main():
    if "--get-pass" in sys.argv:
        # Mode internal: print passphrase untuk dipakai bat file
        print(load_passphrase(), end="")
        return

    print()
    print("=" * 60)
    print("  Setup Auto Runner — Sekali Setup, Jalan Selamanya")
    print("=" * 60)
    print()

    # Cek apakah sudah ada config
    existing = load_passphrase()
    if existing:
        print(f"  [..] Passphrase sudah tersimpan sebelumnya.")
        change = input("  Ganti passphrase? (y/N): ").strip().lower()
        if change != "y":
            print()
        else:
            existing = ""

    if not existing:
        import getpass
        while True:
            pw = getpass.getpass("  Masukkan passphrase identity.pem: ")
            if not pw:
                print("  [ERR] Passphrase tidak boleh kosong!")
                continue

            # Verifikasi passphrase benar dengan mencoba buka identity.pem
            key_path = PROJECT_DIR / "identity.pem"
            if key_path.exists():
                try:
                    sys.path.insert(0, str(PROJECT_DIR))
                    from technocore_agent import load_identity, did_from_private_key
                    pk = load_identity(key_path, pw.encode("utf-8"))
                    did = did_from_private_key(pk)
                    print(f"  [OK] Passphrase benar! DID: {did}")
                    save_passphrase(pw)
                    break
                except Exception as e:
                    print(f"  [ERR] Passphrase salah: {e}")
                    continue
            else:
                print("  [WARN] identity.pem tidak ditemukan, passphrase disimpan tanpa verifikasi.")
                save_passphrase(pw)
                break

    print()
    print("  Pilih mode auto-start:")
    print("  [1] Jalan otomatis saat Windows nyala (startup)")
    print("  [2] Jadwal harian pakai Task Scheduler")
    print("  [3] Jalankan sekarang saja (tanpa auto-start)")
    print()
    mode = input("  Pilihan [1]: ").strip() or "1"

    if mode == "1":
        print()
        if create_startup_bat():
            print()
            print("  [OK] SELESAI! Auto runner akan jalan otomatis setiap PC dinyalakan.")
            print("  [..] Tidak perlu buka terminal lagi.")
            print()
            run_now = input("  Jalankan sekarang juga? (Y/n): ").strip().lower()
            if run_now != "n":
                _run_now()
        else:
            print("  [..] Coba mode lain atau jalankan manual.")

    elif mode == "2":
        _setup_task_scheduler()

    elif mode == "3":
        _run_now()

def _run_now():
    """Jalankan auto_runner sekarang dengan passphrase dari config."""
    pw = load_passphrase()
    if not pw:
        print("  [ERR] Passphrase belum diset. Jalankan setup dulu.")
        return

    python_exe = PROJECT_DIR / ".venv/Scripts/python.exe"
    runner_py  = PROJECT_DIR / "auto_runner.py"

    env = os.environ.copy()
    env["TECHNOCORE_PASS"] = pw
    env["PYTHONIOENCODING"] = "utf-8"

    print()
    print("  Menjalankan auto runner... (Ctrl+C untuk berhenti)")
    print()
    subprocess.run(
        [str(python_exe), str(runner_py), "--interval", "600", "--room", "lobby"],
        env=env,
        cwd=str(PROJECT_DIR),
    )

def _setup_task_scheduler():
    """Buat Windows Task Scheduler task."""
    python_exe = PROJECT_DIR / ".venv/Scripts/pythonw.exe"
    runner_py  = PROJECT_DIR / "auto_runner.py"
    config_py  = PROJECT_DIR / "setup_autorun.py"

    # Buat wrapper bat untuk task scheduler
    bat_path = PROJECT_DIR / "run_task.bat"
    bat_content = f"""@echo off
cd /d "{PROJECT_DIR}"
for /f "delims=" %%P in ('"{PROJECT_DIR}\\.venv\\Scripts\\python.exe" "{config_py}" --get-pass') do set TECHNOCORE_PASS=%%P
"{python_exe}" "{runner_py}" --interval 600 --room lobby
"""
    bat_path.write_text(bat_content, encoding="utf-8")

    # Buat task pakai schtasks
    cmd = [
        "schtasks", "/create", "/tn", "TechnocoreAutoRunner",
        "/tr", str(bat_path),
        "/sc", "daily",
        "/st", "08:00",
        "/f"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("  [OK] Task Scheduler berhasil dibuat!")
        print("  [..] Auto runner akan jalan setiap hari jam 08:00.")
        print(f"  [..] Lihat di: Task Scheduler → TechnocoreAutoRunner")
    else:
        print(f"  [ERR] Gagal buat task: {result.stderr}")
        print(f"  [..] Coba jalankan sebagai Administrator.")

if __name__ == "__main__":
    main()
