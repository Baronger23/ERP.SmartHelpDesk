"""Calendar arithmetic independent of Frappe; all inputs are explicit policy."""
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo


def deadline(anchor, minutes, policy):
    if minutes <= 0:
        raise ValueError("SLA duration must be positive")
    zone = ZoneInfo(policy["timezone"])
    current = datetime.fromisoformat(str(anchor))
    current = current.replace(tzinfo=zone) if current.tzinfo is None else current.astimezone(zone)
    if policy.get("calendar") == "24x7":
        return current + timedelta(minutes=minutes)
    calendar = policy.get("weekly_windows", {})
    holidays = set(policy.get("holidays", []))
    remaining = float(minutes) * 60
    # Bounded search rejects impossible or malformed calendars rather than hanging a worker.
    for _ in range(3660):
        if current.date().isoformat() not in holidays:
            windows = calendar.get(str(current.weekday()), [])
            previous_end = None
            for start, end in sorted(windows):
                begin = datetime.combine(current.date(), time.fromisoformat(start), zone)
                finish = datetime.combine(current.date(), time.fromisoformat(end), zone)
                if finish <= begin or (previous_end and begin < previous_end):
                    raise ValueError("Invalid or overlapping calendar windows")
                previous_end = finish
                cursor = max(current, begin)
                if cursor < finish:
                    seconds = (finish - cursor).total_seconds()
                    if remaining <= seconds:
                        return cursor + timedelta(seconds=remaining)
                    remaining -= seconds
        current = datetime.combine(current.date() + timedelta(days=1), time.min, zone)
    raise ValueError("SLA calendar has insufficient working time")


def validate_policy(policy):
    if policy.get("anchor") not in ("reported_at", "received_at"):
        raise ValueError("Policy must specify reported_at or received_at as anchor")
    if policy.get("pause_policy") != "No pause":
        raise ValueError("P1 supports No pause; waiting is recorded without hiding elapsed SLA")
    for key in ("response_minutes", "restoration_minutes"):
        deadline("2026-01-01 00:00:00", float(policy[key]), policy)
