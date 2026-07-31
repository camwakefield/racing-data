"""Shared helpers: horse-name normalisation and small utilities.

The join key across every source is (normalised horse name, date). Sectionals
come in UPPERCASE, stewards reports in Title Case, and both tack on country
suffixes like "(NZ)" / "(IRE)" inconsistently, so we canonicalise hard.
"""
import re

_COUNTRY = re.compile(r"\s*\((?:NZ|IRE|GB|FR|USA|JPN|AUS|GER|ARG|BRZ|SAF|CHI|ITY|SAU)\)\s*", re.I)
_PUNCT = re.compile(r"[^A-Z0-9 ]")
_WS = re.compile(r"\s+")


def norm_name(name):
    """CUSTOM / Custom / Custom (NZ) / Lollie's Galore  ->  a stable key."""
    if not name:
        return ""
    s = name.upper()
    s = _COUNTRY.sub(" ", s)     # drop (NZ) etc.
    s = s.replace("'", "").replace("`", "")
    s = _PUNCT.sub(" ", s)       # strip remaining punctuation
    s = _WS.sub(" ", s).strip()
    return s


def secs(txt):
    """Seconds from any racing.com split-time format.

    Newer exports use M:SS.mm ('0:14.33'); the older ones use HH:MM:SS.mmm
    ('00:00:08.680'). Handle 1, 2 or 3 colon-separated parts.

        '14.33'        -> 14.33
        '0:14.33'      -> 14.33
        '00:00:08.680' -> 8.68
        '00:01:07.429' -> 67.429
    """
    if txt is None:
        return None
    txt = str(txt).strip()
    if not txt:
        return None
    if ":" in txt:
        total = 0.0
        for part in txt.split(":"):
            total = total * 60 + float(part)
        return round(total, 3)
    return round(float(txt), 3)


def r2(x):
    return None if x is None else round(x, 2)


def norm_date(s):
    """Normalise a date to ISO YYYY-MM-DD. Handles the racing.com CSV's usual
    '2026-07-25 00:00:00' plus Excel-mangled 'DD/MM/YYYY' (Australian order) and
    'YYYY/MM/DD'. Returns the input unchanged if unrecognised."""
    s = (s or "").strip().split(" ")[0].split("T")[0]
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)   # DD/MM/YYYY (AU)
    if m:
        return "%s-%02d-%02d" % (m.group(3), int(m.group(2)), int(m.group(1)))
    m = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", s)
    if m:
        return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))
    return s
