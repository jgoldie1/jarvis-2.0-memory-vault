from __future__ import annotations

from quantum_blockchain.core.ternary_logic import TernaryState


class Contract:
    def __init__(self, name: str = "GenericContract") -> None:
        self.name = name
        self.state = TernaryState.UNKNOWN

    def approve(self) -> None:
        self.state = TernaryState.TRUE

    def reject(self) -> None:
        self.state = TernaryState.FALSE

    def pending(self) -> None:
        self.state = TernaryState.UNKNOWN

    def status(self) -> str:
        return self.state.name
