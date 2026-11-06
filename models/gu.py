from database.validator import Field

GU_INSTANCE_SCHEMA = {
    "instance_id": Field("str"),
    "gu_id": Field("str"),
    "state": Field("str", choices=["stored", "refined"]),
    "created_world_day": Field("float"),
    "refined_world_day": Field("float", nullable=True),
    "last_fed_world_day": Field("float"),
    "vitality": Field("int", min=0, max=100),
    "vital": Field("bool", required=False),
}
