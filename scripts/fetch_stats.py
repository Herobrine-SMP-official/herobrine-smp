import os, json, re, stat, datetime
import paramiko

HOST = os.environ["SFTP_HOST"]
PORT = int(os.environ.get("SFTP_PORT", "22"))
USER = os.environ["SFTP_USER"]
PASS = os.environ["SFTP_PASS"]
WORLD = os.environ.get("WORLD_FOLDER", "world")   # world folder ka naam
ESS = "plugins/Essentials/userdata"

t = paramiko.Transport((HOST, PORT))
t.connect(username=USER, password=PASS)
sftp = paramiko.SFTPClient.from_transport(t)

def read(path):
    with sftp.open(path, "r") as f:
        return f.read().decode("utf-8", "ignore")

# uuid -> name
names = {}
try:
    for u in json.loads(read("usercache.json")):
        names[u["uuid"]] = u["name"]
except Exception as e:
    print("usercache error:", e)

players = []
for fa in sftp.listdir_attr(f"{WORLD}/stats"):
    if not fa.filename.endswith(".json"):
        continue
    uuid = fa.filename[:-5]
    try:
        s = json.loads(read(f"{WORLD}/stats/{fa.filename}")).get("stats", {})
    except Exception:
        continue
    c = s.get("minecraft:custom", {})
    ticks = c.get("minecraft:play_time", c.get("minecraft:play_one_minute", 0))
    mined = sum(s.get("minecraft:mined", {}).values())

    money = 0
    try:
        m = re.search(r"^money:\s*'?([\d.]+)", read(f"{ESS}/{uuid}.yml"), re.M)
        if m:
            money = int(float(m.group(1)))
    except Exception:
        pass

    players.append({
        "name": names.get(uuid, uuid[:8]),
        "money": money,
        "kills": c.get("minecraft:player_kills", 0),
        "mobkills": c.get("minecraft:mob_kills", 0),
        "deaths": c.get("minecraft:deaths", 0),
        "playtime": round(ticks / 72000, 1),   # hours
        "mined": mined,
    })

out = {
    "updated": datetime.datetime.utcnow().isoformat() + "Z",
    "players": players,
}
with open("stats.json", "w") as f:
    json.dump(out, f)
print("Done:", len(players), "players")
