"""
Master script: run all pipeline steps in sequence.

Usage:
    python run_all.py [--skip-instagram]

Steps:
    1. Scrape TikTok
    2. Scrape Instagram  (skipped with --skip-instagram)
    3. Transcribe videos
    4. Extract products with AI
    5. Load into Supabase
"""

import subprocess
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
ROOT_DIR = SCRIPTS_DIR.parents[1]
DATA_DIR = ROOT_DIR / "data"

STEPS = [
    ("1_scrape_tiktok.py", "Scrape TikTok videos"),
    ("2_scrape_instagram.py", "Scrape Instagram reels"),
    ("3_transcribe.py", "Transcribe videos"),
    ("4_extract_products.py", "Extract products with AI"),
    ("5_load_database.py", "Load data into Supabase"),
]

SKIP_INSTAGRAM = "--skip-instagram" in sys.argv


def run_step(script: str, description: str) -> bool:
    """Run a pipeline step. Returns True on success."""
    print(f"\n{'=' * 60}")
    print(f"▶ {description}")
    print(f"  Script: {script}")
    print("=" * 60)

    if script == "2_scrape_instagram.py" and SKIP_INSTAGRAM:
        print("  [SKIP] Instagram scraping disabled (--skip-instagram)")
        return True

    start = time.time()
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script)],
        capture_output=False,
    )
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"\n✅ {description} completed in {elapsed:.1f}s")
        return True
    else:
        print(f"\n❌ {description} failed (exit code {result.returncode})")
        return False


def main():
    print("=" * 60)
    print("🚀 Influencer Product Search — Full Pipeline")
    print("=" * 60)
    if SKIP_INSTAGRAM:
        print("Mode: TikTok only (--skip-instagram)\n")
    else:
        print("Mode: TikTok + Instagram\n")

    DATA_DIR.mkdir(exist_ok=True)

    success_count = 0
    for script, description in STEPS:
        ok = run_step(script, description)
        if ok:
            success_count += 1
        else:
            answer = input(f"\nStep failed. Continue anyway? [y/N] ").strip().lower()
            if answer != "y":
                print("Aborting pipeline.")
                sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"Pipeline complete: {success_count}/{len(STEPS)} steps succeeded")
    print("=" * 60)


if __name__ == "__main__":
    main()
