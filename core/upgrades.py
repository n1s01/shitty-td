from config import GAME_CONFIG, UPGRADES


def level(profile, uid):
    return profile["upgrades"].get(uid, 0)


def _side_ids():
    return [uid for uid, spec in UPGRADES.items() if spec["kind"] == "side"]


def is_unlocked(profile, uid):
    spec = UPGRADES[uid]
    if spec["kind"] != "main":
        return True
    return all(level(profile, sid) >= UPGRADES[sid]["max_level"] for sid in _side_ids())


def is_maxed(profile, uid):
    return level(profile, uid) >= UPGRADES[uid]["max_level"]


def can_buy(profile, uid):
    return (
        is_unlocked(profile, uid)
        and not is_maxed(profile, uid)
        and profile["coins"] >= UPGRADES[uid]["cost"]
    )


def buy(profile, uid):
    if not can_buy(profile, uid):
        return False
    profile["coins"] -= UPGRADES[uid]["cost"]
    profile["upgrades"][uid] = level(profile, uid) + 1
    return True


def effective_stats(profile):
    effects = UPGRADES["tavern"].get("effects", {})
    tavern = level(profile, "tavern")

    base_hp = GAME_CONFIG["tower_max_hp"]
    base_cd = GAME_CONFIG["tower_fire_cooldown"]
    base_dmg = GAME_CONFIG["projectile_damage"]

    hp = round(base_hp * (1 + tavern * effects.get("hp_mult", 0)))
    cooldown = max(1, round(base_cd * (1 + tavern * effects.get("cooldown_mult", 0))))
    damage = base_dmg * (1 + tavern * effects.get("damage_mult", 0))

    return {
        "tower_max_hp": hp,
        "tower_fire_cooldown": cooldown,
        "projectile_damage": damage,
        "auto_fire": level(profile, "auto_fire") >= 1,
        "auto_wave": level(profile, "auto_wave") >= 1,
        "auto_collect": level(profile, "auto_collect") >= 1,
        "obstacle_breaks": level(profile, "break_obstacle"),
    }
