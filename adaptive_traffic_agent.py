"""Adaptive traffic-signal controller for the Meet the Builders demo.

This module intentionally does NOT replace the security layer.  It only improves
normal congestion handling by adapting the duration of existing SUMO phases.
Because it never jumps directly between arbitrary green phases, SUMO's configured
yellow/clearance phases remain in the loop.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import traci


@dataclass
class LaneSnapshot:
    lane_id: str
    vehicles: int
    halting: int
    waiting_time: float


class AdaptiveTrafficSignalAgent:
    """One adaptive controller per SUMO traffic light."""

    def __init__(
        self,
        intersection_id: str,
        min_green: float = 8.0,
        max_green: float = 45.0,
        low_demand_threshold: int = 2,
        high_demand_threshold: int = 8,
        imbalance_ratio: float = 2.0,
    ) -> None:
        self.intersection_id = intersection_id
        self.min_green = min_green
        self.max_green = max_green
        self.low_demand_threshold = low_demand_threshold
        self.high_demand_threshold = high_demand_threshold
        self.imbalance_ratio = imbalance_ratio

        self.controlled_lanes = list(dict.fromkeys(
            traci.trafficlight.getControlledLanes(intersection_id)
        ))
        self._last_phase = traci.trafficlight.getPhase(intersection_id)
        self._phase_started_at = traci.simulation.getTime()

    def _lane_snapshot(self, lane_id: str) -> LaneSnapshot:
        return LaneSnapshot(
            lane_id=lane_id,
            vehicles=traci.lane.getLastStepVehicleNumber(lane_id),
            halting=traci.lane.getLastStepHaltingNumber(lane_id),
            waiting_time=traci.lane.getWaitingTime(lane_id),
        )

    def _snapshots(self) -> Dict[str, LaneSnapshot]:
        return {lane: self._lane_snapshot(lane) for lane in self.controlled_lanes}

    def _phase_state(self) -> str:
        logic = traci.trafficlight.getAllProgramLogics(self.intersection_id)[0]
        phase_index = traci.trafficlight.getPhase(self.intersection_id)
        return logic.phases[phase_index].state

    def _green_lanes(self, phase_state: str) -> List[str]:
        """Map green signal indices to their incoming lanes using controlled links."""
        links = traci.trafficlight.getControlledLinks(self.intersection_id)
        green = []
        for signal_index, link_group in enumerate(links):
            if signal_index >= len(phase_state) or phase_state[signal_index] not in "Gg":
                continue
            for link in link_group:
                if link and link[0] not in green:
                    green.append(link[0])
        return green

    @staticmethod
    def _demand(lanes: List[str], snapshots: Dict[str, LaneSnapshot]) -> float:
        # Halting vehicles are weighted most heavily; waiting time breaks ties.
        return sum(
            2.0 * snapshots[l].halting
            + 0.5 * snapshots[l].vehicles
            + 0.02 * snapshots[l].waiting_time
            for l in lanes
            if l in snapshots
        )

    def _emergency_on_controlled_lane(self) -> bool:
        for vehicle_id in traci.vehicle.getIDList():
            try:
                if traci.vehicle.getTypeID(vehicle_id) != "emergency":
                    continue
                if traci.vehicle.getLaneID(vehicle_id) in self.controlled_lanes:
                    return True
            except traci.TraCIException:
                continue
        return False

    def observe(self) -> dict:
        now = traci.simulation.getTime()
        phase = traci.trafficlight.getPhase(self.intersection_id)
        if phase != self._last_phase:
            self._last_phase = phase
            self._phase_started_at = now

        state = self._phase_state()
        snapshots = self._snapshots()
        green_lanes = self._green_lanes(state)
        red_lanes = [lane for lane in self.controlled_lanes if lane not in green_lanes]

        return {
            "time": now,
            "phase": phase,
            "phase_state": state,
            "phase_age": now - self._phase_started_at,
            "snapshots": snapshots,
            "green_lanes": green_lanes,
            "red_lanes": red_lanes,
            "green_demand": self._demand(green_lanes, snapshots),
            "red_demand": self._demand(red_lanes, snapshots),
            "green_halting": sum(snapshots[l].halting for l in green_lanes),
            "red_halting": sum(snapshots[l].halting for l in red_lanes),
            "emergency_present": self._emergency_on_controlled_lane(),
        }

    def adapt(self) -> Tuple[str, dict]:
        """Adapt the *duration* of the current phase; never jump across safety phases."""
        obs = self.observe()
        state = obs["phase_state"]

        # Do not interfere with yellow/all-red/transition phases.
        if "G" not in state and "g" not in state:
            return "TRANSITION_UNCHANGED", obs

        age = obs["phase_age"]
        green_q = obs["green_halting"]
        red_q = obs["red_halting"]
        green_demand = max(obs["green_demand"], 0.1)
        red_demand = obs["red_demand"]

        # Preserve minimum green for stability and safe operation.
        if age < self.min_green:
            return "MIN_GREEN", obs

        # If an emergency is already on a currently served approach, keep green briefly.
        if obs["emergency_present"] and green_q > 0:
            traci.trafficlight.setPhaseDuration(self.intersection_id, 5.0)
            return "EMERGENCY_HOLD", obs

        # Core Meet-the-Builders scenario:
        # nearly empty green approach + heavily queued red approaches -> finish green soon.
        severe_imbalance = (
            green_q <= self.low_demand_threshold
            and red_q >= self.high_demand_threshold
            and red_demand >= self.imbalance_ratio * green_demand
        )
        if severe_imbalance:
            # SUMO will proceed to the configured next phase, including yellow clearance.
            traci.trafficlight.setPhaseDuration(self.intersection_id, 1.0)
            return "SHORTEN_GREEN", obs

        # Busy served movement: allow a modest extension, but never indefinitely.
        if green_q >= self.high_demand_threshold and age < self.max_green:
            remaining_cap = max(1.0, self.max_green - age)
            traci.trafficlight.setPhaseDuration(
                self.intersection_id, min(5.0, remaining_cap)
            )
            return "EXTEND_GREEN", obs

        # Hard cap prevents starvation of other approaches.
        if age >= self.max_green:
            traci.trafficlight.setPhaseDuration(self.intersection_id, 1.0)
            return "MAX_GREEN_REACHED", obs

        return "KEEP", obs

    def reward(self) -> float:
        snapshots = self._snapshots()
        queue = sum(x.halting for x in snapshots.values())
        waiting = sum(x.waiting_time for x in snapshots.values())
        return -(queue + 0.5 * waiting)
