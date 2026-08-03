#!/usr/bin/env python3
"""
probe/pf_reach.py -- can a GitHub Actions runner reach the Punting Form API?

WHY THIS EXISTS
---------------
Today every API call runs on Cameron's Mac, because api.puntingform.com.au is
unreachable from the Claude cloud sandbox. That makes one laptop a single point
of failure for the whole capture pipeline. A GitHub Actions runner has plain
outbound internet and already runs on every push. Nobody has ever tested whether
it can reach Punting Form. If it can, capture becomes scheduled and unattended,
and the Mac stops being load-bearing.

SECURITY
--------
The API key is NEVER committed. It is read from the environment variable
PF_API_KEY, which the workflow populates from secrets.PF_API_KEY. This script
must never print the key, and never write it into any output file. The `redact`
helper below is applied to every line before it is written.

OUTPUT
------
    probe/out/pf_reach.txt   human-readable report, committed back to the repo
    probe/out/*.json         small sample payloads (key-free)

Nothing is written to data/. The Action that runs this must not touch data/.

PAPER TRADING ONLY.
"""

import json, os, sys, time, datetime, socket, urllib.request, urllib.error

KEY  = os.environ.get("PF_API_KEY", "")
HOST = "https://api.puntingform.com.au"
OUT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

LINES = []


def redact(s):
    s = str(s)
    if KEY:
        s = s.replace(KEY, "<PF_API_KEY>")
    return s


def say(*a):
    line = redact(" ".join(str(x) for x in a))
    print(line)
    LINES.append(line)


def get(path, **params):
    """Return (status, payload_or_None, elapsed_seconds)."""
    params["apiKey"] = KEY
    q = "&".join("%s=%s" % (k, v) for k, v in params.items())
    url = "%s/%s?%s" % (HOST, path.lstrip("/"), q)
    t0 = time.time()
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            body = r.read().decode("utf-8", "replace")
            try:
                return r.getcode(), json.loads(body), time.time() - t0
            except Exception:
                return r.getcode(), {"_raw": body[:400]}, time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, None, time.time() - t0
    except urllib.error.URLError as e:
        return "URLError: %s" % redact(e.reason), None, time.time() - t0
    except Exception as e:
        return "%s: %s" % (type(e).__name__, redact(e)), None, time.time() - t0


say("PAPER TRADING ONLY")
say("pf_reach probe -- run at %s UTC" % datetime.datetime.utcnow().isoformat(timespec="seconds"))
say("runner: %s" % sys.platform)
say("")

if not KEY:
    say("!! PF_API_KEY is empty.")
    say("   The repository secret has not been set, so this run tests DNS and TCP")
    say("   only. Set it at Settings -> Secrets and variables -> Actions ->")
    say("   New repository secret, name PF_API_KEY, then re-run this workflow.")
    say("")

# ---------------------------------------------------------------- 1. DNS
say("=" * 66)
say("1. DNS")
say("=" * 66)
try:
    infos = socket.getaddrinfo("api.puntingform.com.au", 443, proto=socket.IPPROTO_TCP)
    addrs = sorted({i[4][0] for i in infos})
    say("   resolves to: %s" % ", ".join(addrs))
except Exception as e:
    say("   FAILED: %s: %s" % (type(e).__name__, e))

# ---------------------------------------------------------------- 2. TCP+TLS
say("")
say("=" * 66)
say("2. TCP + TLS handshake on 443")
say("=" * 66)
try:
    import ssl
    ctx = ssl.create_default_context()
    with socket.create_connection(("api.puntingform.com.au", 443), timeout=20) as s:
        with ctx.wrap_socket(s, server_hostname="api.puntingform.com.au") as ss:
            cert = ss.getpeercert()
            say("   TLS ok, protocol %s" % ss.version())
            say("   cert notAfter: %s" % cert.get("notAfter"))
except Exception as e:
    say("   FAILED: %s: %s" % (type(e).__name__, e))

# ---------------------------------------------------------------- 3. calls
say("")
say("=" * 66)
say("3. authenticated endpoint calls")
say("=" * 66)

today = datetime.date.today()
CALLS = [
    ("form/meetingslist  today    ", "v2/form/meetingslist", dict(meetingDate=today.isoformat())),
    ("form/meetingslist  tomorrow ", "v2/form/meetingslist", dict(meetingDate=(today + datetime.timedelta(days=1)).isoformat())),
    ("form/meetingslist  -60 days ", "v2/form/meetingslist", dict(meetingDate=(today - datetime.timedelta(days=60)).isoformat())),
]

first_meeting = None
for label, path, params in CALLS:
    code, js, dt = get(path, **params)
    n = ""
    if isinstance(js, dict):
        pl = js.get("payLoad")
        if isinstance(pl, list):
            n = "%d meetings" % len(pl)
            if pl and first_meeting is None:
                first_meeting = pl[0]
        elif isinstance(pl, dict):
            n = "payLoad dict"
        if js.get("error"):
            n += "  error=%s" % redact(js["error"])
    say("   %s HTTP %-6s %5.2fs  %s" % (label, code, dt, n))
    time.sleep(0.3)

# ---------------------------------------------------------------- 4. flucs
say("")
say("=" * 66)
say("4. does a form line carry flucs (the whole point)")
say("=" * 66)

mid = None
if first_meeting:
    mid = str(first_meeting.get("meetingId") or "")
    tr = (first_meeting.get("track") or {}).get("name")
    say("   using meetingId %s (%s)" % (mid, tr))

if mid:
    code, js, dt = get("v2/form/form", meetingId=mid, raceNumber=1, runs=10)
    say("   form/form -> HTTP %s in %.2fs" % (code, dt))
    lines = []
    if isinstance(js, dict):
        for rc in ((js.get("payLoad") or {}).get("races") or []):
            for rn in (rc.get("runners") or []):
                for fl in (rn.get("forms") or []):
                    lines.append(fl)
    say("   historical form lines returned: %d" % len(lines))
    if lines:
        keys = sorted(lines[0].keys())
        say("   form-line keys: %s" % ", ".join(keys))
        for k in ("flucs", "priceSP", "priceBF", "priceTAB", "inRun", "hasSectionalData"):
            nn = [f.get(k) for f in lines if f.get(k) not in (None, "", 0)]
            say("     %-16s populated %4d/%4d  e.g. %s" % (k, len(nn), len(lines), redact(nn[:3])))
        with open(os.path.join(OUT, "form_line_sample.json"), "w") as f:
            json.dump(lines[0], f, indent=2, default=str)
        say("   wrote probe/out/form_line_sample.json")
else:
    say("   no meeting id available -- skipped")

# ---------------------------------------------------------------- 5. verdict
say("")
say("=" * 66)
say("5. verdict")
say("=" * 66)
ok = any("HTTP 200" in l for l in LINES)
if ok:
    say("   The GitHub Actions runner CAN reach the Punting Form API.")
    say("   Capture can move off the Mac and run on a schedule.")
else:
    say("   No successful authenticated call. Either the key is unset, the key is")
    say("   rejected from this IP, or the host is unreachable from GitHub's network.")
    say("   Read sections 1-3 above to tell which.")
say("")
say("PAPER TRADING ONLY")

with open(os.path.join(OUT, "pf_reach.txt"), "w") as f:
    f.write("\n".join(LINES) + "\n")
print("\nwrote probe/out/pf_reach.txt")
