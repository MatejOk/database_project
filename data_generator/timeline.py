from datetime import date, datetime, time, timedelta
from random import Random

import holidays

WORKDAY_START = time(7, 0)
WORKDAY_END = time(16, 0)

POLISH_HOLIDAYS = holidays.country_holidays("PL")


def working_days(first_day: date, last_day: date) -> list[date]:
    days = []
    day = first_day
    while day <= last_day:
        if day.weekday() < 5 and day not in POLISH_HOLIDAYS:
            days.append(day)
        day += timedelta(days=1)
    return days


def random_moment(rng: Random, day: date) -> datetime:
    shift_seconds = (WORKDAY_END.hour - WORKDAY_START.hour) * 3600
    return datetime.combine(day, WORKDAY_START) + timedelta(seconds=rng.randrange(shift_seconds))


def random_moment_between(rng: Random, first_day: date, last_day: date) -> datetime:
    return random_moment(rng, rng.choice(working_days(first_day, last_day)))
