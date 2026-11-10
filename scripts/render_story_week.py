#!/usr/bin/env python3
"""Render a week's two daily Muslim World story posts for TikTok scheduling.

The same story order matches the local YouTube autopilot: YouTube posts at
12:30/18:30, TikTok Studio is planned for 13:00/19:00 Europe/Berlin.
This script only renders files; it never uploads or schedules posts.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import history  # noqa: E402
import story_short  # noqa: E402
from story_bank import all_stories  # noqa: E402

TZ = ZoneInfo("Europe/Berlin")
OUT = SRC / "output"


def build_schedule(start: date, days: int, per_day: int) -> list[dict]:
    fresh = [
        s for s in all_stories()
        if s["title"].strip().lower() not in history.all_titles()
    ]
    count = days * per_day
    if len(fresh) < count:
        raise RuntimeError(f"Only {len(fresh)} fresh stories; need {count}. Refill src/story_bank.py.")
    posts = []
    for i, story in enumerate(fresh[:count]):
        day = start + timedelta(days=i // per_day)
        slot = i % per_day
        if per_day == 2:
            yt_time, tt_time = (("12:30", "13:00"), ("18:30", "19:00"))[slot]
        else:
            hour = 12 + (6 * slot)
            yt_time = f"{hour:02d}:30"
            tt_time = f"{hour:02d}:55"
        posts.append({
            "date": day.isoformat(),
            "timezone": "Europe/Berlin",
            "youtube_time": yt_time,
            "tiktok_time": tt_time,
            "story_id": story["id"],
            "title": story["title"],
            "source": story["ending"]["source"],
            "status": "pending_render",
            "video": None,
        })
    return posts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-date", help="First posting date, YYYY-MM-DD (default: tomorrow in Berlin)")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--per-day", type=int, default=2)
    ap.add_argument("--resume", action="store_true", help="Continue an existing week manifest")
    args = ap.parse_args()

    start = date.fromisoformat(args.start_date) if args.start_date else datetime.now(TZ).date() + timedelta(days=1)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = OUT / f"story_week_{start.isoformat()}.json"

    if manifest.exists():
        if not args.resume:
            raise FileExistsError(f"{manifest} exists; use --resume to continue it.")
        plan = json.loads(manifest.read_text())
        posts = plan["posts"]
    else:
        posts = build_schedule(start, args.days, args.per_day)
        plan = {
            "start_date": start.isoformat(),
            "days": args.days,
            "posts_per_day": args.per_day,
            "timezone": "Europe/Berlin",
            "posts": posts,
        }
        manifest.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")

    for i, post in enumerate(posts, 1):
        old = post.get("video")
        if post.get("status") == "rendered" and old and Path(old).is_file():
            print(f"[{i}/{len(posts)}] already rendered: {post['story_id']} -> {old}", flush=True)
            continue
        print(f"[{i}/{len(posts)}] {post['date']} TikTok {post['tiktok_time']} — {post['story_id']}", flush=True)
        try:
            video = story_short.run(story_id=post["story_id"], dry_run=True)
            if not video or not Path(video).is_file():
                raise RuntimeError("renderer returned no video file")
            post["video"] = str(Path(video).resolve())
            post["status"] = "rendered"
            post.pop("error", None)
            manifest.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
            print(f"    ready: {post['video']}", flush=True)
        except Exception as exc:
            post["status"] = "render_failed"
            post["error"] = str(exc)
            manifest.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
            raise
    print(f"Manifest: {manifest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
