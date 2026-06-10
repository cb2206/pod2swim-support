#!/usr/bin/env python3
"""Point pod2swim.com at GitHub Pages via the Porkbun API.

Sets up the DNS records GitHub Pages needs for a custom apex domain:
  - apex  (pod2swim.com)   ALIAS -> cb2206.github.io
  - www   (www.pod2swim.com) CNAME -> cb2206.github.io
and removes Porkbun's default parking records that would conflict.

Credentials are read from the environment or a local, git-ignored file
(scripts/.porkbun.env) with two lines:
    PORKBUN_API_KEY=pk1_...
    PORKBUN_SECRET_KEY=sk1_...
Generate them at Porkbun → Account → API Access, and toggle "API Access"
ON for the domain (Domain Management → details → API Access).

Usage:
    python3 scripts/porkbun_dns.py            # dry run: show plan, change nothing
    python3 scripts/porkbun_dns.py --apply    # actually delete + create records
"""
import json, os, sys, urllib.request

API = "https://api.porkbun.com/api/json/v3"
DOMAIN = "pod2swim.com"
TARGET = "cb2206.github.io"          # GitHub Pages host for user cb2206
HOSTS = {"", "www"}                  # records we manage (apex + www)
MANAGED_TYPES = {"A", "AAAA", "ALIAS", "CNAME"}
HERE = os.path.dirname(os.path.abspath(__file__))


def load_creds():
    key = os.environ.get("PORKBUN_API_KEY")
    sec = os.environ.get("PORKBUN_SECRET_KEY")
    envfile = os.path.join(HERE, ".porkbun.env")
    if (not key or not sec) and os.path.exists(envfile):
        for line in open(envfile):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k == "PORKBUN_API_KEY":
                key = key or v
            elif k == "PORKBUN_SECRET_KEY":
                sec = sec or v
    if not key or not sec:
        sys.exit("Missing credentials. Set PORKBUN_API_KEY and PORKBUN_SECRET_KEY "
                 "in the environment or scripts/.porkbun.env")
    return key, sec


def call(path, key, sec, extra=None):
    body = {"apikey": key, "secretapikey": sec}
    if extra:
        body.update(extra)
    req = urllib.request.Request(
        f"{API}/{path}", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read()).get("message", "")
        except Exception:
            msg = ""
        raise RuntimeError(f"{path}: HTTP {e.code} {msg}".rstrip())
    if data.get("status") != "SUCCESS":
        raise RuntimeError(f"{path}: {data.get('message', data)}")
    return data


def short(name):
    """Full record name -> Porkbun 'name' (subdomain part; '' for apex)."""
    if name == DOMAIN:
        return ""
    if name.endswith("." + DOMAIN):
        return name[: -(len(DOMAIN) + 1)]
    return name


def main():
    apply = "--apply" in sys.argv
    key, sec = load_creds()

    ip = call("ping", key, sec).get("yourIp")
    print(f"Authenticated with Porkbun (your IP: {ip})")

    records = call(f"dns/retrieve/{DOMAIN}", key, sec).get("records", [])
    print(f"\nCurrent records for {DOMAIN}: {len(records)}")
    for r in records:
        print(f"  [{r['id']}] {r['type']:6} {r['name'] or '@':24} -> {r['content']}")

    # records to remove: apex/www of a managed type that aren't already correct
    to_delete = [
        r for r in records
        if short(r["name"]) in HOSTS and r["type"] in MANAGED_TYPES
        and not (short(r["name"]) == "" and r["type"] == "ALIAS" and r["content"] == TARGET)
        and not (short(r["name"]) == "www" and r["type"] == "CNAME" and r["content"] == TARGET)
    ]
    have_apex = any(short(r["name"]) == "" and r["type"] == "ALIAS" and r["content"] == TARGET for r in records)
    have_www = any(short(r["name"]) == "www" and r["type"] == "CNAME" and r["content"] == TARGET for r in records)

    to_create = []
    if not have_apex:
        to_create.append({"name": "", "type": "ALIAS", "content": TARGET, "ttl": "600"})
    if not have_www:
        to_create.append({"name": "www", "type": "CNAME", "content": TARGET, "ttl": "600"})

    print("\nPlan:")
    for r in to_delete:
        print(f"  DELETE [{r['id']}] {r['type']} {r['name'] or '@'} -> {r['content']}")
    for r in to_create:
        print(f"  CREATE {r['type']} {r['name'] or '@'} -> {r['content']}")
    if not to_delete and not to_create:
        print("  (nothing to do — DNS already correct)")

    if not apply:
        print("\nDry run. Re-run with --apply to make these changes.")
        return

    for r in to_delete:
        call(f"dns/delete/{DOMAIN}/{r['id']}", key, sec)
        print(f"  deleted [{r['id']}]")
    for r in to_create:
        call(f"dns/create/{DOMAIN}", key, sec, r)
        print(f"  created {r['type']} {r['name'] or '@'} -> {r['content']}")
    print("\nDone. DNS can take a few minutes to a few hours to propagate.")


if __name__ == "__main__":
    main()
