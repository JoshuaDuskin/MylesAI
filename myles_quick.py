from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QuickLookupResult:
    kind: str
    answer: str = ""
    evidence: str = ""
    source_urls: tuple[str, ...] = ()
    error: str = ""


_LOCAL_WORK_MARKERS = (
    "file", "folder", "repo", "repository", "github", "dashboard", "code",
    "script", "powershell", "terminal", "install", "deploy", "publish", "build",
    "edit", "modify", "fix", "repair", "download", "move", "delete", "rename",
    "logs", "log file", "tower", "computer", "windows", "myles runtime",
)

_WEATHER_MARKERS = (
    "weather", "forecast", "temperature", "temp", "rain", "snow",
    "storm", "wind", "humidity",
)

_PUBLIC_LOOKUP_MARKERS = (
    "latest", "current", "today", "tomorrow", "news", "score", "scores",
    "price", "prices", "weather", "forecast", "look up", "lookup",
    "search for", "google", "find out",
)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def is_weather_request(text: str) -> bool:
    t = normalize_text(text)
    return bool(t) and any(marker in t for marker in _WEATHER_MARKERS)


def looks_like_quick_public_lookup(text: str) -> bool:
    """Conservative fast-path detector for public, read-only information.

    These requests should be answered in the conversation turn. They must not
    become durable owner jobs just because fresh information requires an HTTP
    lookup.
    """
    t = normalize_text(text)
    if not t:
        return False
    if any(marker in t for marker in _LOCAL_WORK_MARKERS):
        return False
    if is_weather_request(t):
        return True
    if not any(marker in t for marker in _PUBLIC_LOOKUP_MARKERS):
        return False

    questionish = (
        "?" in str(text or "")
        or t.startswith(("what ", "who ", "where ", "when ", "how ", "give me ", "tell me ", "find "))
    )
    return questionish


_US_STATE_ABBR = {
    "al":"Alabama","ak":"Alaska","az":"Arizona","ar":"Arkansas","ca":"California",
    "co":"Colorado","ct":"Connecticut","de":"Delaware","fl":"Florida","ga":"Georgia",
    "hi":"Hawaii","id":"Idaho","il":"Illinois","in":"Indiana","ia":"Iowa",
    "ks":"Kansas","ky":"Kentucky","la":"Louisiana","me":"Maine","md":"Maryland",
    "ma":"Massachusetts","mi":"Michigan","mn":"Minnesota","ms":"Mississippi","mo":"Missouri",
    "mt":"Montana","ne":"Nebraska","nv":"Nevada","nh":"New Hampshire","nj":"New Jersey",
    "nm":"New Mexico","ny":"New York","nc":"North Carolina","nd":"North Dakota","oh":"Ohio",
    "ok":"Oklahoma","or":"Oregon","pa":"Pennsylvania","ri":"Rhode Island","sc":"South Carolina",
    "sd":"South Dakota","tn":"Tennessee","tx":"Texas","ut":"Utah","vt":"Vermont",
    "va":"Virginia","wa":"Washington","wv":"West Virginia","wi":"Wisconsin","wy":"Wyoming",
    "dc":"District of Columbia",
}

_WEATHER_TIME_TAIL = re.compile(
    r"(?:\s+(?:for\s+)?(?:today|tomorrow|tonight|this\s+(?:morning|afternoon|evening|week)|"
    r"next\s+(?:week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday))+$",
    flags=re.I,
)

def _normalize_weather_location(value: str) -> str:
    loc = re.sub(r"\s+", " ", str(value or "").strip(" ,.;:!?"))
    loc = _WEATHER_TIME_TAIL.sub("", loc).strip(" ,.;:!?")
    # Remove conversational tails that are not part of a place.
    loc = re.sub(r"(?i)\s+(?:please|pls|thanks|thank you)$", "", loc).strip(" ,")
    parts = loc.split()
    if parts:
        last = re.sub(r"[^A-Za-z]", "", parts[-1]).lower()
        if last in _US_STATE_ABBR:
            parts[-1] = _US_STATE_ABBR[last]
            loc = " ".join(parts)
    return loc

def _weather_location_variants(location: str) -> list[str]:
    loc = _normalize_weather_location(location)
    if not loc:
        return []
    variants = [loc]
    # Open-Meteo's geocoder is more reliable when broad city search and state
    # filtering are separated, so also try city-only for "City State".
    state_names = {v.lower() for v in _US_STATE_ABBR.values()}
    pieces = loc.split()
    if len(pieces) >= 2:
        for n in (2, 1):
            if len(pieces) > n:
                tail = " ".join(pieces[-n:]).lower()
                if tail in state_names:
                    city = " ".join(pieces[:-n]).strip()
                    if city and city not in variants:
                        variants.append(city)
                    break
    return variants

def _extract_weather_location(text: str) -> str:
    raw = re.sub(r"\s+", " ", str(text or "").strip())
    # Prefer an explicit "in <place>" tail, which handles:
    # "weather for tomorrow in Lebanon Missouri".
    m = re.search(r"\bin\s+(.+?)(?:[?.!]|$)", raw, flags=re.I)
    if m:
        loc = _normalize_weather_location(m.group(1))
        if loc:
            return loc

    # Handle "weather for Lebanon Missouri tomorrow" / "forecast for X".
    m = re.search(
        r"\b(?:weather|forecast|temperature|temp)\s+(?:for\s+)?(.+?)(?:\s+(?:today|tomorrow|tonight|this week|next week))?(?:[?.!]|$)",
        raw,
        flags=re.I,
    )
    if m:
        loc = _normalize_weather_location(m.group(1))
        if loc and loc.lower() not in {"today", "tomorrow", "tonight"}:
            return loc

    return ""


def _requested_weather_day(text: str) -> str:
    t = normalize_text(text)
    if "tomorrow" in t:
        return "tomorrow"
    if "tonight" in t:
        return "today"
    return "today"


_WEATHER_CODES = {
    0: "clear",
    1: "mostly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "foggy",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    56: "freezing drizzle",
    57: "freezing drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "freezing rain",
    67: "freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light rain showers",
    81: "rain showers",
    82: "heavy rain showers",
    85: "snow showers",
    86: "heavy snow showers",
    95: "thunderstorms",
    96: "thunderstorms with hail",
    99: "strong thunderstorms with hail",
}


def _weather_description(code: Any) -> str:
    try:
        return _WEATHER_CODES.get(int(code), "mixed conditions")
    except Exception:
        return "mixed conditions"


def _format_num(value: Any) -> str:
    try:
        n = float(value)
        if abs(n - round(n)) < 0.05:
            return str(int(round(n)))
        return f"{n:.1f}"
    except Exception:
        return "-"


def _format_weather_payload(
    geo: dict[str, Any],
    forecast: dict[str, Any],
    requested_day: str,
) -> str:
    daily = forecast.get("daily") or {}
    times = list(daily.get("time") or [])
    idx = 1 if requested_day == "tomorrow" else 0
    if not times or idx >= len(times):
        raise ValueError("forecast did not include the requested day")

    def at(name: str, default=None):
        values = daily.get(name) or []
        return values[idx] if idx < len(values) else default

    place = str(geo.get("name") or "").strip()
    admin = str(geo.get("admin1") or "").strip()
    country_code = str(geo.get("country_code") or "").strip()
    location_parts = [x for x in (place, admin) if x]
    location = ", ".join(location_parts) or "that location"
    if country_code and country_code.upper() != "US" and country_code not in location:
        location += f", {country_code}"

    label = "Tomorrow" if requested_day == "tomorrow" else "Today"
    condition = _weather_description(at("weather_code"))
    high = _format_num(at("temperature_2m_max"))
    low = _format_num(at("temperature_2m_min"))
    rain = _format_num(at("precipitation_probability_max"))
    wind = _format_num(at("wind_speed_10m_max"))

    pieces = [f"{label} in {location}: {condition}, high {high}°F, low {low}°F."]
    if rain != "-":
        pieces.append(f"Rain chance {rain}%.")
    if wind != "-":
        pieces.append(f"Winds up to {wind} mph.")
    return " ".join(pieces)


def _json_get(url: str, timeout: int = 15) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Myles/9.4 local-assistant",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def weather_lookup(text: str) -> QuickLookupResult:
    location = _extract_weather_location(text)
    if not location:
        return QuickLookupResult(
            kind="weather",
            error="I need a city or location for the weather lookup.",
        )

    try:
        results: list[dict[str, Any]] = []
        for query in _weather_location_variants(location):
            geo_url = (
                "https://geocoding-api.open-meteo.com/v1/search?"
                + urllib.parse.urlencode(
                    {"name": query, "count": 10, "language": "en", "format": "json"}
                )
            )
            geo_data = _json_get(geo_url, timeout=12)
            results = list(geo_data.get("results") or [])
            if results:
                break

        if not results:
            # Weather remains a conversational lookup. Fall back to bounded web
            # evidence instead of turning a failed geocoder into a background job.
            fallback = web_search(f"weather forecast {_requested_weather_day(text)} {location}", max_results=5)
            if fallback.evidence:
                return QuickLookupResult(
                    kind="weather_web_fallback",
                    evidence=fallback.evidence,
                    source_urls=fallback.source_urls,
                    error=f"Direct weather geocoding could not match {location}.",
                )
            return QuickLookupResult(
                kind="weather",
                error=f"I couldn't find a weather location matching {location}.",
            )

        # Prefer a US/state match when the owner supplied a state.
        geo = results[0]
        location_low = location.lower()
        desired_state = ""
        for state_name in _US_STATE_ABBR.values():
            if state_name.lower() in location_low:
                desired_state = state_name.lower()
                break

        best_score = -1
        for candidate in results:
            admin = str(candidate.get("admin1") or "").lower()
            country = str(candidate.get("country_code") or "").upper()
            name = str(candidate.get("name") or "").lower()
            score = 0
            if country == "US":
                score += 3
            if desired_state and admin == desired_state:
                score += 8
            if name and name in location_low:
                score += 4
            if score > best_score:
                best_score = score
                geo = candidate

        params = {
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "daily": ",".join(
                [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                ]
            ),
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
            "forecast_days": 3,
        }
        forecast_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
        forecast = _json_get(forecast_url, timeout=12)
        day = _requested_weather_day(text)
        answer = _format_weather_payload(geo, forecast, day)
        return QuickLookupResult(
            kind="weather",
            answer=answer,
            source_urls=("https://open-meteo.com/",),
        )
    except Exception as exc:
        return QuickLookupResult(kind="weather", error=f"Weather lookup failed: {type(exc).__name__}: {exc}")


def _strip_tags(value: str) -> str:
    value = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def web_search(text: str, max_results: int = 5) -> QuickLookupResult:
    """Small read-only search path for simple public questions.

    This intentionally returns evidence rather than pretending a search result is
    itself a verified answer. The conversation model summarizes the evidence.
    """
    query = str(text or "").strip()
    if not query:
        return QuickLookupResult(kind="web_search", error="No search query was supplied.")
    try:
        url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Myles/9.4",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            page = r.read().decode("utf-8", errors="replace")

        # Keep parsing deliberately simple and bounded.
        blocks = re.findall(r'(?is)<div[^>]+class="result results_links.*?</div>\s*</div>', page)
        rows = []
        urls = []
        for block in blocks[: max(1, min(int(max_results), 8))]:
            link = re.search(r'(?is)<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block)
            if not link:
                continue
            href = html.unescape(link.group(1))
            title = _strip_tags(link.group(2))
            snippet_m = re.search(r'(?is)<a[^>]+class="result__snippet"[^>]*>(.*?)</a>|<div[^>]+class="result__snippet"[^>]*>(.*?)</div>', block)
            snippet = _strip_tags((snippet_m.group(1) or snippet_m.group(2)) if snippet_m else "")
            if href.startswith("//duckduckgo.com/l/?"):
                parsed = urllib.parse.urlparse("https:" + href)
                target = urllib.parse.parse_qs(parsed.query).get("uddg", [""])[0]
                if target:
                    href = urllib.parse.unquote(target)
            if not href.startswith("http"):
                continue
            urls.append(href)
            rows.append(f"{len(rows)+1}. {title}\n{snippet}\n{href}".strip())
        if not rows:
            return QuickLookupResult(kind="web_search", error="The quick web search returned no usable results.")
        return QuickLookupResult(
            kind="web_search",
            evidence="\n\n".join(rows),
            source_urls=tuple(urls),
        )
    except Exception as exc:
        return QuickLookupResult(kind="web_search", error=f"Quick web search failed: {type(exc).__name__}: {exc}")


def quick_lookup(text: str) -> QuickLookupResult:
    if is_weather_request(text):
        return weather_lookup(text)
    return web_search(text)
