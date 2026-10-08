"""Tiny dependency-free recurrent brain with neuromodulated plasticity."""

from __future__ import annotations

import math
import random


class TinyBrain:
    def __init__(self, size: int = 16, seed: int = 7):
        rng = random.Random(seed)
        self.size = size
        self.state = [0.0] * size
        self.recurrent = [[rng.uniform(-0.11, 0.11) for _ in range(size)] for _ in range(size)]
        self.sensory = [[rng.uniform(-0.18, 0.18) for _ in range(6)] for _ in range(size)]
        self.motor = [[rng.uniform(-0.10, 0.10) for _ in range(size)] for _ in range(2)]
        self.eligibility = [[0.0] * size for _ in range(2)]
        self.expected_reward = 0.0
        self.hormones = {"dopamine": 12.0, "octopamine": 22.0, "hunger": 55.0, "stress": 4.0, "caffeine": 0.0}

    def step(self, features: list[float]) -> tuple[float, float]:
        new_state = []
        for i in range(self.size):
            recurrent_drive = sum(w * x for w, x in zip(self.recurrent[i], self.state))
            sensory_drive = sum(w * x for w, x in zip(self.sensory[i], features))
            new_state.append(math.tanh(recurrent_drive + sensory_drive))
        self.state = new_state
        motors = [math.tanh(sum(w * x for w, x in zip(row, self.state))) for row in self.motor]
        for m in range(2):
            for i in range(self.size):
                self.eligibility[m][i] = 0.96 * self.eligibility[m][i] + motors[m] * self.state[i]
        arousal = 0.55 + 0.004 * self.hormones["octopamine"] + 0.002 * self.hormones["caffeine"]
        return motors[0] * arousal, motors[1] * arousal

    def reward(self, value: float) -> None:
        prediction_error = value - self.expected_reward
        self.expected_reward += 0.04 * prediction_error
        self.hormones["dopamine"] = min(100.0, max(0.0, self.hormones["dopamine"] * 0.92 + prediction_error * 36))
        learning_rate = 0.00035
        for m in range(2):
            for i in range(self.size):
                self.motor[m][i] += learning_rate * prediction_error * self.eligibility[m][i]

    def apply_effects(self, effects: dict[str, float]) -> None:
        for name, amount in effects.items():
            if name in self.hormones:
                self.hormones[name] = min(100.0, max(0.0, self.hormones[name] + amount))

    def tick_body(self, dt: float) -> None:
        h = self.hormones
        h["hunger"] = min(100.0, h["hunger"] + dt * 0.12)
        h["dopamine"] *= 0.995 ** (dt * 10)
        h["octopamine"] *= 0.998 ** (dt * 10)
        h["caffeine"] *= 0.999 ** (dt * 10)
        h["stress"] *= 0.999 ** (dt * 10)
