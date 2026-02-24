"""
Script 3: Transcribe videos that don't already have captions.

Usage:
    python 3_transcribe.py

For videos scraped from TikTok that already have captions this script is a
no-op (it just copies the existing caption text).  For Instagram videos (or
TikTok videos without captions) it uses OpenAI Whisper to transcribe.

Requires:
    openai-whisper  (pip install openai-whisper)
    ffmpeg          (system package)
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

TIKTOK_FILE = DATA_DIR / "tiktok_videos.json"
INSTAGRAM_FILE = DATA_DIR / "instagram_videos.json"
OUTPUT_FILE = DATA_DIR / "transcripts.json"

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny / base / small / medium / large


def transcribe_video(model, video_path: str) -> str:
    """Run Whisper on a local video file and return the transcript."""
    try:
        result = model.transcribe(video_path, language=None)  # auto-detect Arabic/English
        return result.get("text", "").strip()
    except Exception as exc:
        print(f"    [WARN] Whisper failed for {video_path}: {exc}")
        return ""


def main():
    print("=" * 60)
    print("Step 3: Transcribing videos")
    print("=" * 60)

    # Collect all video records
    all_videos: list[dict] = []

    if TIKTOK_FILE.exists():
        with open(TIKTOK_FILE) as f:
            all_videos.extend(json.load(f))
        print(f"Loaded {len(all_videos)} TikTok records")
    else:
        print("[WARN] No tiktok_videos.json found — run script 1 first")

    if INSTAGRAM_FILE.exists():
        with open(INSTAGRAM_FILE) as f:
            insta = json.load(f)
        all_videos.extend(insta)
        print(f"Loaded {len(insta)} Instagram records")

    if not all_videos:
        print("[ERROR] No video records found. Run scripts 1 and/or 2 first.")
        return

    # Separate videos that already have captions from those that need Whisper
    with_caption = [v for v in all_videos if v.get("has_caption") and v.get("caption")]
    needs_transcription = [v for v in all_videos if not (v.get("has_caption") and v.get("caption"))]

    print(f"\n{len(with_caption)} videos already have captions (no transcription needed)")
    print(f"{len(needs_transcription)} videos need transcription\n")

    transcripts: list[dict] = []

    # Copy over existing captions
    for v in with_caption:
        transcripts.append(
            {
                "id": v.get("id") or v.get("shortcode"),
                "influencer": v["influencer"],
                "platform": v["platform"],
                "url": v.get("url", ""),
                "transcript": v["caption"],
                "source": "caption",
            }
        )

    # Transcribe remaining videos with Whisper
    if needs_transcription:
        try:
            import whisper
        except ImportError:
            print("[ERROR] openai-whisper not installed. Run: pip install openai-whisper")
            print("Saving only captioned videos …")
        else:
            print(f"Loading Whisper model '{WHISPER_MODEL}' …")
            model = whisper.load_model(WHISPER_MODEL)
            print("Model loaded\n")

            for i, v in enumerate(needs_transcription, 1):
                local_path = v.get("local_path", "")
                print(f"[{i}/{len(needs_transcription)}] Transcribing {v['influencer']} — {local_path}")

                if not local_path or not Path(local_path).exists():
                    print("    [SKIP] Video file not found")
                    continue

                text = transcribe_video(model, local_path)
                transcripts.append(
                    {
                        "id": v.get("id") or v.get("shortcode"),
                        "influencer": v["influencer"],
                        "platform": v["platform"],
                        "url": v.get("url", ""),
                        "transcript": text,
                        "source": "whisper",
                    }
                )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(transcripts, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(transcripts)} transcripts to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
