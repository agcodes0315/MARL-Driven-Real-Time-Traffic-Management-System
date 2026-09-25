from __future__ import annotations

import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

CSV_FILE = Path("adaptive_demo_results.csv")
OUTPUT_FILE = Path("gemini_traffic_analysis.md")
MODEL = "gemini-3.8-flash"


def fnum(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def summarize_csv(path):
    if not path.exists():
        raise FileNotFoundError(
            "adaptive_demo_results.csv was not found. "
            "Run: python run_adaptive_demo.py --steps 5000"
        )

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        raise ValueError("adaptive_demo_results.csv is empty.")

    required = {
        "step", "time", "intersection", "action",
        "green_halting", "red_halting",
        "green_demand", "red_demand", "reward"
    }
    missing = required - set(rows[0])
    if missing:
        raise ValueError("Missing CSV columns: " + ", ".join(sorted(missing)))

    grouped = defaultdict(list)
    for row in rows:
        grouped[row["intersection"]].append(row)

    per_intersection = {}
    for name, items in sorted(grouped.items()):
        green_q = [fnum(r["green_halting"]) for r in items]
        red_q = [fnum(r["red_halting"]) for r in items]
        rewards = [fnum(r["reward"]) for r in items]

        per_intersection[name] = {
            "records": len(items),
            "avg_green_halting": round(mean(green_q), 2),
            "avg_red_halting": round(mean(red_q), 2),
            "max_green_halting": round(max(green_q), 2),
            "max_red_halting": round(max(red_q), 2),
            "avg_reward": round(mean(rewards), 3),
            "actions": dict(Counter(r["action"] for r in items)),
        }

    all_green = [fnum(r["green_halting"]) for r in rows]
    all_red = [fnum(r["red_halting"]) for r in rows]
    all_rewards = [fnum(r["reward"]) for r in rows]

    return {
        "source": path.name,
        "records": len(rows),
        "simulation_steps_observed": len({r["step"] for r in rows}),
        "intersections_observed": len(grouped),
        "overall": {
            "avg_green_halting": round(mean(all_green), 2),
            "avg_red_halting": round(mean(all_red), 2),
            "max_green_halting": round(max(all_green), 2),
            "max_red_halting": round(max(all_red), 2),
            "avg_reward": round(mean(all_rewards), 3),
            "actions": dict(Counter(r["action"] for r in rows)),
        },
        "per_intersection": per_intersection,
    }


def make_prompt(summary):
    return """You are an advisory traffic-operations analysis assistant.

The data below comes from a SUMO adaptive traffic-control simulation.
Analyze ONLY the supplied aggregate metrics.

Rules:
- Do not invent data, locations, causes, or performance improvements.
- Do not claim this controller beats fixed timing; no comparative benchmark
  is supplied here.
- Do not issue traffic-light commands.
- Explain useful congestion patterns and controller-action patterns.
- Suggest what a human operator/researcher should investigate.
- Clearly state that these are simulation observations, not live municipal data.

Return concise Markdown with exactly these headings:
# Gemini Traffic Operations Analysis
## Executive Summary
## Congestion Observations
## Controller Behaviour
## Intersections Requiring Attention
## Suggested Investigation
## Safety and Scope Note

SIMULATION SUMMARY:
""" + json.dumps(summary, indent=2)


def call_gemini(summary):
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is not set.")

    from google import genai

    client = genai.Client()
    try:
        interaction = client.interactions.create(
            model=MODEL,
            input=make_prompt(summary),
        )
        text = interaction.output_text
        if not text or not text.strip():
            raise RuntimeError("Gemini returned an empty response.")
        return text.strip()
    finally:
        client.close()


def fallback_report(summary, reason):
    o = summary["overall"]
    actions = ", ".join(
        f"{name}: {count}" for name, count in o["actions"].items()
    )
    return f"""# Local Traffic Operations Analysis (Gemini Fallback)

Gemini was unavailable, so this report was generated locally.

## Executive Summary
- Records: **{summary["records"]}**
- Intersections: **{summary["intersections_observed"]}**
- Average green-side halted vehicles: **{o["avg_green_halting"]}**
- Average red-side halted vehicles: **{o["avg_red_halting"]}**
- Maximum red-side halted queue: **{o["max_red_halting"]}**

## Controller Behaviour
Recorded actions: {actions}.

## Suggested Investigation
Inspect sustained queues and compare this run against a controlled fixed-timing
baseline using equivalent demand and per-vehicle waiting/travel-time metrics.

## Safety and Scope Note
These are SUMO simulation observations. This analyzer is advisory only and
does not control traffic signals.

Fallback reason: `{reason}`
"""


def main():
    print("Loading adaptive traffic simulation results...")

    try:
        summary = summarize_csv(CSV_FILE)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"Records: {summary['records']}")
    print(f"Intersections: {summary['intersections_observed']}")
    print(f"Gemini model: {MODEL}")

    try:
        report = call_gemini(summary)
        mode = "Gemini API"
        print("Gemini traffic analysis completed successfully.")
    except Exception as exc:
        mode = "Local deterministic fallback"
        print(f"Gemini unavailable: {type(exc).__name__}: {exc}")
        print("Using fallback.")
        report = fallback_report(summary, f"{type(exc).__name__}: {exc}")

    metadata = (
        "<!--\n"
        "Generated by gemini_traffic_analyzer.py\n"
        f"Mode: {mode}\n"
        f"Model: {MODEL}\n"
        f"Source: {CSV_FILE.name}\n"
        "-->\n\n"
    )

    OUTPUT_FILE.write_text(metadata + report + "\n", encoding="utf-8")

    print(f"Analysis saved to: {OUTPUT_FILE.resolve()}")
    print(f"Mode used: {mode}")
    print("Safety: Gemini is advisory only and does not control traffic signals.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
