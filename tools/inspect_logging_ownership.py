"""Read-only inspection of logging-camp ownership in a plaintext Victoria 3 save."""
from pathlib import Path
import json
import re
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8-sig")

def database(key):
    start = re.search(r"(?m)^" + re.escape(key) + r"=\{", text).end()
    depth = 1
    end = start
    for token in re.finditer(r'"(?:\\.|[^"\\])*"|[{}]', text[start:]):
        if token[0] == "{":
            depth += 1
        elif token[0] == "}":
            depth -= 1
        if depth == 0:
            end = start + token.start()
            break
    section = text[start:end]
    return {int(m[1]): m[2] for m in re.finditer(r"(?ms)^(\d+)=\{\n(.*?)^\}", section)}

def value(body, key):
    match = re.search(r"(?m)^\t" + re.escape(key) + r"=([^\n]+)", body)
    return match[1].strip() if match else None

def number(body, key):
    raw = value(body, key)
    return int(raw) if raw and raw.isdigit() else None

buildings = database("building_manager")
states = database("states")
countries = database("country_manager")
ownership = database("building_ownership_manager")
country_tags = {cid: value(body, "definition") or value(body, "tag") for cid, body in countries.items()}
report = {"save": str(path), "buildings": len(buildings), "states": len(states), "logging_camps": 0, "broken_logging_camps": []}
for bid, body in buildings.items():
    if value(body, "building") != "building_logging_camp":
        continue
    report["logging_camps"] += 1
    state_id = number(body, "state")
    issues = []
    if state_id not in states:
        issues.append({"issue": "logging camp has missing state", "state": state_id})
    owners_raw = value(body, "owners") or ""
    for oid in map(int, re.findall(r"\d+", owners_raw)):
        record = ownership.get(oid)
        if record is None:
            issues.append({"issue": "missing ownership record", "ownership_id": oid})
            continue
        ident = re.search(r"(?s)\tidentity=\{(.*?)\n\t\}", record)
        if not ident:
            issues.append({"issue": "missing ownership identity", "ownership_id": oid})
            continue
        owner_building = re.search(r"\bbuilding=(\d+)", ident[1])
        owner_country = re.search(r"\bcountry=(\d+)", ident[1])
        if owner_building:
            obid = int(owner_building[1])
            obody = buildings.get(obid)
            osid = number(obody, "state") if obody else None
            if osid not in states:
                issues.append({"issue": "owner building has missing state", "ownership_id": oid, "owner_building": obid, "owner_type": value(obody, "building") if obody else None, "owner_state": osid, "levels": number(record, "levels")})
        elif owner_country:
            cid = int(owner_country[1])
            if cid not in countries:
                issues.append({"issue": "missing owning country", "ownership_id": oid, "country": cid})
        else:
            issues.append({"issue": "unrecognized identity", "ownership_id": oid, "identity": ident[1]})
    if issues:
        state = states.get(state_id, "")
        report["broken_logging_camps"].append({"building": bid, "state": state_id, "state_region": value(state, "region") or value(state, "definition"), "country": country_tags.get(number(state, "country")), "levels": number(body, "levels"), "issues": issues})
out = Path(__file__).with_name("zip_bomb_save_ownership_report.json")
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
assert states and countries and buildings and ownership, "Failed to parse a save database"
print(json.dumps({k: v for k, v in report.items() if k != "broken_logging_camps"}, indent=2))
print("Broken logging camps:", len(report["broken_logging_camps"]))
print(json.dumps(report["broken_logging_camps"][:15], indent=2))
