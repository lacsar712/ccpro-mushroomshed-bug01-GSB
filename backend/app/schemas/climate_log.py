from marshmallow import Schema, fields, validate

from app.utils import dt_to_json


class ClimateLogCreateSchema(Schema):
    room_id = fields.Int(required=True, data_key="roomId")
    recorded_at = fields.Raw(required=True, data_key="recordedAt")
    temp_c = fields.Float(required=True, data_key="tempC")
    humidity_pct = fields.Int(
        required=True,
        data_key="humidityPct",
        validate=validate.Range(min=1, max=100, error="humidityPct 须在 1–100 之间"),
    )
    co2_ppm = fields.Float(allow_none=True, data_key="co2Ppm")
    notes = fields.Str(allow_none=True)


class ClimateLogOutSchema(Schema):
    id = fields.Int(dump_only=True)
    room_id = fields.Int(data_key="roomId")
    recorded_at = fields.Method("dump_recorded_at", data_key="recordedAt")
    temp_c = fields.Float(data_key="tempC")
    humidity_pct = fields.Int(data_key="humidityPct")
    co2_ppm = fields.Float(allow_none=True, data_key="co2Ppm")
    notes = fields.Str(allow_none=True)

    def dump_recorded_at(self, obj):
        v = obj.recorded_at if hasattr(obj, "recorded_at") else obj["recorded_at"]
        return dt_to_json(v)
