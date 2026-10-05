from __future__ import annotations
import time
from enum import Enum
from typing import Any, Dict, Optional


class CircuitState(str, Enum):
    CLOSED = "CLOSED"        # Normal operation: JEV requests allowed
    OPEN = "OPEN"            # Tripped: JEV requests blocked, instant fallback to native
    HALF_OPEN = "HALF_OPEN"  # Testing: 1 probe request allowed to test service health


class JevCircuitBreaker:
    """
    High-speed Circuit Breaker for JEV capability.
    Prevents IDE/MCP workflows from hanging on repeated JEV timeouts or service outages.
    """

    def __init__(
        self,
        max_consecutive_failures: int = 3,
        cooldown_seconds: float = 60.0,
    ):
        self.max_failures = max(1, max_consecutive_failures)
        self.cooldown_seconds = max(0.01, float(cooldown_seconds))
        self._state: CircuitState = CircuitState.CLOSED
        self._consecutive_failures: int = 0
        self._last_state_change: float = time.time()
        self._last_failure_time: Optional[float] = None
        self._total_trips: int = 0
        self._total_successes: int = 0
        self._total_failures: int = 0

    @property
    def state(self) -> CircuitState:
        # Check if OPEN cooldown has expired -> transition to HALF_OPEN
        if self._state == CircuitState.OPEN:
            if (time.time() - self._last_state_change) >= self.cooldown_seconds:
                self._state = CircuitState.HALF_OPEN
                self._last_state_change = time.time()
        return self._state

    def allow_request(self) -> bool:
        """
        Determines whether a JEV invocation should proceed or immediately fail over.
        """
        current = self.state
        return current in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        """
        Records a successful JEV call. Resets failure count and closes circuit if probing.
        """
        self._total_successes += 1
        self._consecutive_failures = 0
        if self._state != CircuitState.CLOSED:
            self._state = CircuitState.CLOSED
            self._last_state_change = time.time()

    def record_failure(self, error: Optional[Exception] = None) -> None:
        """
        Records a failed JEV call or timeout. Trips circuit to OPEN if threshold reached.
        """
        self._total_failures += 1
        self._consecutive_failures += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN or self._consecutive_failures >= self.max_failures:
            if self._state != CircuitState.OPEN:
                self._state = CircuitState.OPEN
                self._last_state_change = time.time()
                self._total_trips += 1

    def reset(self) -> None:
        """
        Manually resets the circuit breaker to CLOSED.
        """
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._last_state_change = time.time()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "consecutive_failures": self._consecutive_failures,
            "max_failures": self.max_failures,
            "cooldown_seconds": self.cooldown_seconds,
            "total_trips": self._total_trips,
            "total_successes": self._total_successes,
            "total_failures": self._total_failures,
            "last_failure_time": self._last_failure_time,
            "time_in_current_state_s": round(time.time() - self._last_state_change, 1),
        }
