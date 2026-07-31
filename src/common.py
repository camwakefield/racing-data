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
    """'0:14.33' -> 14.33 ; '14.33' -> 14.33 ; '' -> None."""
    if txt is None:
        return None
    txt = str(txt).strip()
    if not txt:
        return None
    if ":" in txt:
        m, s = txt.split(":")
        return round(int(m) * 60 + float(s), 3)
    return round(float(txt), 3)


def r2(x):
    return None if x is None else round(x, 2)
