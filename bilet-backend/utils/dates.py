import calendar as calendar_module
import re
from datetime import date, timedelta

from constants.events import MONTH_ALIASES
from utils.text import contains_any, normalize_text_for_intent


def year_for_month(month, today=None):
    today = today or date.today()
    if today.month <= month:
        return today.year
    return today.year + 1


def month_date_range(month, week_number=None, today=None):
    year = year_for_month(month, today)
    last_day = calendar_module.monthrange(year, month)[1]

    if week_number:
        start_day = min(1 + ((week_number - 1) * 7), last_day)
        end_day = min(start_day + 6, last_day)
    else:
        start_day = 1
        end_day = last_day

    return {
        "start_date": date(year, month, start_day).isoformat(),
        "end_date": date(year, month, end_day).isoformat(),
    }


def date_range_from_day_months(start_day, start_month, end_day, end_month):
    start_year = year_for_month(start_month)
    end_year = year_for_month(end_month)

    start_last_day = calendar_module.monthrange(start_year, start_month)[1]
    end_last_day = calendar_module.monthrange(end_year, end_month)[1]
    if start_day < 1 or start_day > start_last_day or end_day < 1 or end_day > end_last_day:
        return None

    start = date(start_year, start_month, start_day)
    end = date(end_year, end_month, end_day)
    if end < start:
        end = date(end.year + 1, end.month, end.day)

    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }


def detect_week_number_from_text(normalized_text):
    week_phrases = [
        (1, ["ilk hafta", "birinci hafta", "1. hafta", "1 hafta"]),
        (2, ["ikinci hafta", "2. hafta"]),
        (3, ["ucuncu hafta", "üçüncü hafta", "3. hafta"]),
        (4, ["dorduncu hafta", "dördüncü hafta", "4. hafta", "son hafta"]),
    ]

    for week_number, phrases in week_phrases:
        if any(normalize_text_for_intent(phrase) in normalized_text for phrase in phrases):
            return week_number

    return None


def normalized_month_aliases():
    aliases = {}
    for month_name, month_number in MONTH_ALIASES.items():
        aliases[normalize_text_for_intent(month_name)] = month_number
    return aliases


def month_regex_pattern():
    aliases = normalized_month_aliases()
    return "|".join(
        re.escape(month_name)
        for month_name in sorted(aliases, key=len, reverse=True)
    )


def detect_compact_same_month_range(normalized_text):
    aliases = normalized_month_aliases()
    month_pattern = month_regex_pattern()
    pattern = rf"\b([0-3]?\d)\s*(?:-|/|ile|ve)\s*([0-3]?\d)\s*({month_pattern})\w*\b"
    match = re.search(pattern, normalized_text)
    if not match:
        return None

    start_day = int(match.group(1))
    end_day = int(match.group(2))
    month = aliases[match.group(3)]
    return date_range_from_day_months(start_day, month, end_day, month)


def day_month_mentions(normalized_text):
    aliases = normalized_month_aliases()
    month_pattern = month_regex_pattern()
    mentions = []

    patterns = [
        rf"\b([0-3]?\d)\s*(?:\.|-)?\s*({month_pattern})\w*\b",
    ]

    seen_spans = set()
    for pattern in patterns:
        for match in re.finditer(pattern, normalized_text):
            if match.span() in seen_spans:
                continue
            seen_spans.add(match.span())
            first, second = match.groups()
            if first.isdigit():
                day = int(first)
                month = aliases[second]
            else:
                month = aliases[first]
                day = int(second)
            mentions.append({
                "day": day,
                "month": month,
                "index": match.start(),
            })

    return sorted(mentions, key=lambda item: item["index"])


def detect_explicit_date_range_from_text(normalized_text):
    compact_range = detect_compact_same_month_range(normalized_text)
    if compact_range:
        return compact_range

    range_words = ["arasi", "arasinda", "arasina", "kadar", "ile", "den", "dan", "ten", "tan", "-"]
    mentions = day_month_mentions(normalized_text)
    if len(mentions) < 2 or not contains_any(normalized_text, range_words):
        return None

    start = mentions[0]
    end = mentions[1]
    return date_range_from_day_months(
        start["day"],
        start["month"],
        end["day"],
        end["month"],
    )


def detect_specific_day_month_from_text(normalized_text):
    aliases = normalized_month_aliases()
    month_pattern = month_regex_pattern()

    patterns = [
        rf"\b([0-3]?\d)\s*(?:\.|-)?\s*({month_pattern})\w*\b",
        rf"\b({month_pattern})\w*\s*([0-3]?\d)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized_text)
        if not match:
            continue

        first, second = match.groups()
        if first.isdigit():
            day = int(first)
            month = aliases[second]
        else:
            month = aliases[first]
            day = int(second)

        year = year_for_month(month)
        last_day = calendar_module.monthrange(year, month)[1]
        if day < 1 or day > last_day:
            return None

        exact_date = date(year, month, day).isoformat()
        return {
            "start_date": exact_date,
            "end_date": exact_date,
        }

    return None


def detect_date_range_from_text(normalized_text):
    today = date.today()

    if "bugun" in normalized_text or "bugün" in normalized_text:
        return {
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
        }

    if "yarin" in normalized_text or "yarın" in normalized_text:
        tomorrow = today + timedelta(days=1)
        return {
            "start_date": tomorrow.isoformat(),
            "end_date": tomorrow.isoformat(),
        }

    if "gelecek hafta" in normalized_text:
        start = today + timedelta(days=7)
        end = start + timedelta(days=6)
        return {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }

    if "bu hafta" in normalized_text or "hafta sonu" in normalized_text or "haftasonu" in normalized_text:
        end = today + timedelta(days=6)
        return {
            "start_date": today.isoformat(),
            "end_date": end.isoformat(),
        }

    explicit_range = detect_explicit_date_range_from_text(normalized_text)
    if explicit_range:
        return explicit_range

    specific_day = detect_specific_day_month_from_text(normalized_text)
    if specific_day:
        return specific_day

    week_number = detect_week_number_from_text(normalized_text)
    for month_name, month_number in normalized_month_aliases().items():
        if month_name in normalized_text:
            return month_date_range(month_number, week_number)

    return None


def latest_message_has_date_hint(normalized_text):
    date_words = [
        "bugun", "bugün", "yarin", "yarın", "hafta", "haftasonu", "hafta sonu",
        "bu ay", "gelecek ay", "pazartesi", "sali", "salı",
        "carsamba", "çarşamba", "persembe", "perşembe", "cuma", "cumartesi",
        "pazar",
    ]
    month_words = [normalize_text_for_intent(month_name) for month_name in MONTH_ALIASES]
    return any(word in normalized_text for word in date_words + month_words)
