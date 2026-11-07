from database.validator import Field

CULTIVATION_SCHEMA = {
    "rank": Field("int", min=1, max=5),
    "stage": Field("int", min=0, max=3),
    "essence": Field("float", min=0),
    "essence_updated_day": Field("float"),
    "foundation": Field("float", min=0, max=100),
}

CHARACTER_SCHEMA = {
    "id": Field("str"),
    "discord_id": Field("int"),
    "name": Field("str"),
    "gender": Field("str", choices=["nam", "nu"]),
    "birth_world_day": Field("float"),
    "awakened_world_day": Field("float"),
    "aptitude": Field("dict", schema={"grade": Field("str"), "ratio": Field("float", min=0.01, max=1.0), "steps": Field("int", min=0, max=50, required=False)}),
    "physique": Field("str", nullable=True),
    "lifespan_years": Field("int", min=1),
    "status": Field("str", choices=["alive", "dead"]),
    "death": Field("dict", nullable=True),
    "cultivation": Field("dict", schema=CULTIVATION_SCHEMA),
    "location": Field("dict", schema={"region": Field("str")}),
    "resources": Field("dict"),
    "gu_ids": Field("list", items=Field("str")),
    "cooldowns": Field("dict"),
    "travel": Field("dict", nullable=True, required=False),
    "notices": Field("list", required=False, items=Field("str")),
    "experience": Field("dict", required=False),
    "ascension": Field("dict", nullable=True, required=False),
    "immortal": Field("dict", nullable=True, required=False),
}
