"""Navigation state transition history for the dashboard."""

from __future__ import annotations

from collections import deque
from typing import Any

from .models import NavigationState


class NavigationStateMachine:
    def __init__(self) -> None:
        self.current = NavigationState.INITIALIZING
        self.history: deque[NavigationState] = deque(maxlen=5)
        self.history.append(self.current)

    def update(self, requested: NavigationState) -> NavigationState:
        if requested != self.current:
            self.current = requested
            self.history.append(requested)
        return self.current

    @property
    def transition_text(self) -> str:
        return " → ".join(state.value for state in self.history)

