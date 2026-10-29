"""Trade Protection Simulation Package.

Provides the MEV Detection and Trade Protection Simulation Engine (Module 1).
Simulates front-running, sandwich attacks, and the effectiveness of various
protection mechanisms on DeFi trades.

Public interface:
    TradeProtectionService.simulate(request) -> SimulationResult
"""

from app.services.trade_protection.trade_protection_service import (
    TradeProtectionService,
)

__all__ = ["TradeProtectionService"]
