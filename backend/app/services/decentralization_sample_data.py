"""Illustrative Sample Datasets for Decentralization Analysis.

This module provides deterministic, synthetic sample datasets designed specifically
for academic demonstration and manual verification.

CRITICAL DISCLAIMER:
These datasets are labeled as 'illustrative_sample'. They represent synthetic,
fictional observations and DO NOT depict real-world, live, or historical Ethereum
builder shares, relay market distribution, or MEV-Boost statistics.

WORKED VERIFICATION EXAMPLE (Builders):
---------------------------------------
Total observed blocks: 450 + 280 + 150 + 80 + 30 + 10 = 1,000 blocks.

Market Shares:
- builder_alpha:   450 / 1000 = 45.0%
- builder_beta:    280 / 1000 = 28.0%
- builder_gamma:   150 / 1000 = 15.0%
- builder_delta:    80 / 1000 =  8.0%
- builder_epsilon:  30 / 1000 =  3.0%
- builder_zeta:     10 / 1000 =  1.0%

Metrics:
- Largest Builder Share: 45.0% (builder_alpha)
- Top-Three Builder Share: 45.0% + 28.0% + 15.0% = 88.0%
- Herfindahl–Hirschman Index (HHI):
    HHI = 45^2 + 28^2 + 15^2 + 8^2 + 3^2 + 1^2
        = 2025 + 784 + 225 + 64 + 9 + 1
        = 3,108 (High concentration according to analytical thresholds)
- Builder Diversity: 6 distinct builders

WORKED VERIFICATION EXAMPLE (Relays):
-------------------------------------
Total observed blocks: 600 + 250 + 150 = 1,000 blocks.

Market Shares:
- relay_one:   600 / 1000 = 60.0%
- relay_two:   250 / 1000 = 25.0%
- relay_three: 150 / 1000 = 15.0%

Metrics:
- Largest Relay Share: 60.0% (relay_one)
- Top-Three Relay Share: 60.0% + 25.0% + 15.0% = 100.0%
- Herfindahl–Hirschman Index (HHI):
    HHI = 60^2 + 25^2 + 15^2
        = 3600 + 625 + 225
        = 4,450 (High concentration according to analytical thresholds)
- Relay Diversity: 3 distinct relays
"""

from typing import Any, Dict, List

SAMPLE_SOURCE_TYPE: str = "illustrative_sample"
SAMPLE_MEASUREMENT_WINDOW: str = "Synthetic Academic Demo Window (1,000 Sample Blocks)"

ILLUSTRATIVE_BUILDERS: List[Dict[str, Any]] = [
    {
        "builder_id": "builder_alpha",
        "display_name": "Alpha Block Builder (Simulated)",
        "block_count": 450,
    },
    {
        "builder_id": "builder_beta",
        "display_name": "Beta Flash Construction (Simulated)",
        "block_count": 280,
    },
    {
        "builder_id": "builder_gamma",
        "display_name": "Gamma Neutral Engine (Simulated)",
        "block_count": 150,
    },
    {
        "builder_id": "builder_delta",
        "display_name": "Delta Community Pool (Simulated)",
        "block_count": 80,
    },
    {
        "builder_id": "builder_epsilon",
        "display_name": "Epsilon Solo Node (Simulated)",
        "block_count": 30,
    },
    {
        "builder_id": "builder_zeta",
        "display_name": "Zeta Experimental Rig (Simulated)",
        "block_count": 10,
    },
]

ILLUSTRATIVE_RELAYS: List[Dict[str, Any]] = [
    {
        "relay_id": "relay_one",
        "display_name": "Prime Relay (Simulated)",
        "block_count": 600,
    },
    {
        "relay_id": "relay_two",
        "display_name": "Nexus Relay (Simulated)",
        "block_count": 250,
    },
    {
        "relay_id": "relay_three",
        "display_name": "Beacon Relay (Simulated)",
        "block_count": 150,
    },
]


def get_illustrative_dataset() -> Dict[str, Any]:
    """Returns a deep-copyable copy of the academic sample dataset."""
    return {
        "source_type": SAMPLE_SOURCE_TYPE,
        "measurement_window": SAMPLE_MEASUREMENT_WINDOW,
        "builder_observations": [dict(b) for b in ILLUSTRATIVE_BUILDERS],
        "relay_observations": [dict(r) for r in ILLUSTRATIVE_RELAYS],
        "verification_reference": {
            "builders": {
                "total_blocks": 1000,
                "largest_share_pct": 45.0,
                "top_three_share_pct": 88.0,
                "hhi": 3108.0,
                "diversity_count": 6,
            },
            "relays": {
                "total_blocks": 1000,
                "largest_share_pct": 60.0,
                "top_three_share_pct": 100.0,
                "hhi": 4450.0,
                "diversity_count": 3,
            },
        },
    }
