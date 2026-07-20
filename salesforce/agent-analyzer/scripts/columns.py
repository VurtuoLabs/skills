#!/usr/bin/env python3
"""
Fixed CSV column definitions for the feature-parity validation pipeline.

The CSV has a fixed schema — no auto-detection needed:
  Session_Number, Turn_Order, User_Utterance, Legacy_Agent_Name,
  Script_Agent_Bundle, Target_Org, Action_Mode
"""

REQUIRED_COLUMNS = [
    "Session_Number",
    "Turn_Order",
    "User_Utterance",
    "Legacy_Agent_Name",
    "Script_Agent_Bundle",
    "Target_Org",
    "Action_Mode",
]


def _norm(s):
    return (s or "").strip().lower().replace(" ", "_")


def validate(fieldnames):
    """Validate that all required columns are present (case/space-insensitive).
    Returns a mapping of normalized_name -> actual_header."""
    norm_map = {}
    for f in fieldnames:
        if f is not None:
            norm_map[_norm(f)] = f

    resolved = {}
    missing = []
    for col in REQUIRED_COLUMNS:
        actual = norm_map.get(_norm(col))
        if actual:
            resolved[_norm(col)] = actual
        else:
            missing.append(col)

    if missing:
        raise SystemExit(
            f"CSV missing required column(s): {', '.join(missing)}. "
            f"Available columns: {', '.join(f for f in fieldnames if f)}")

    return resolved
