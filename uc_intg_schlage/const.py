"""Constants for the Schlage lock integration."""

STATE_ON = "ON"
STATE_UNAVAILABLE = "UNAVAILABLE"

POLL_INTERVAL = 30

STATUS_LOCKED = "Locked"
STATUS_UNLOCKED = "Unlocked"
STATUS_JAMMED = "Jammed"
STATUS_UNKNOWN = "Unknown"

# Auto-lock presets (seconds -> label). The device's own value is added if not listed.
AUTO_LOCK_PRESETS = [
    (0, "Off"),
    (15, "15 seconds"),
    (30, "30 seconds"),
    (60, "1 minute"),
    (120, "2 minutes"),
    (240, "4 minutes"),
    (300, "5 minutes"),
]
