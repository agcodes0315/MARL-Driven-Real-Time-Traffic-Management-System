"""Run the adaptive congestion demo against the repository's final2.sumocfg."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import traci

from adaptive_traffic_agent import AdaptiveTrafficSignalAgent


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="final2.sumocfg", help="Path to SUMO .sumocfg")
    p.add_argument("--steps", type=int, default=37172)
    p.add_argument("--nogui", action="store_true", help="Use sumo instead of sumo-gui")
    p.add_argument("--decision-interval", type=int, default=5)
    p.add_argument("--output", default="adaptive_demo_results.csv")
    return p.parse_args()


def main():
    args = parse_args()
    config = Path(args.config).resolve()
    if not config.exists():
        raise FileNotFoundError(f"SUMO config not found: {config}")

    binary = "sumo" if args.nogui else "sumo-gui"
    traci.start([binary, "-c", str(config)])

    try:
        traffic_lights = list(traci.trafficlight.getIDList())
        agents = {tl: AdaptiveTrafficSignalAgent(tl) for tl in traffic_lights}

        rows = []
        action_counts = {}

        for step in range(args.steps):
            traci.simulationStep()

            if step % args.decision_interval != 0:
                continue

            for tl, agent in agents.items():
                action, obs = agent.adapt()
                action_counts[action] = action_counts.get(action, 0) + 1
                reward = agent.reward()

                rows.append({
                    "step": step,
                    "time": obs["time"],
                    "intersection": tl,
                    "phase": obs["phase"],
                    "action": action,
                    "green_halting": obs["green_halting"],
                    "red_halting": obs["red_halting"],
                    "green_demand": round(obs["green_demand"], 2),
                    "red_demand": round(obs["red_demand"], 2),
                    "emergency_present": int(obs["emergency_present"]),
                    "reward": round(reward, 2),
                })

                if action in {"SHORTEN_GREEN", "EXTEND_GREEN", "EMERGENCY_HOLD", "MAX_GREEN_REACHED"}:
                    print(
                        f"[{step:05d}] {tl}: {action:<18} | "
                        f"green queue={obs['green_halting']:>2} | "
                        f"red queue={obs['red_halting']:>2} | "
                        f"phase={obs['phase']}"
                    )

        if rows:
            with open(args.output, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        print("\n=== Adaptive demo complete ===")
        print(f"Traffic lights: {len(traffic_lights)}")
        print(f"CSV: {Path(args.output).resolve()}")
        print("Actions:")
        for action, count in sorted(action_counts.items()):
            print(f"  {action}: {count}")

    finally:
        traci.close()


if __name__ == "__main__":
    main()
