from marshmallow import Schema, fields, validate

from app.utils import dt_to_json


class FlushHarvestCreateSchema(Schema):
    room_id = fields.Int(required=True, data_key="roomId")
    harvested_at = fields.Raw(required=True, data_key="harvestedAt")
    flush_no = fields.Int(required=True, data_key="flushNo", validate=validate.Range(min=1))
    weight_kg = fields.Float(
        required=True,
        data_key="weightKg",
        validate=validate.Range(min=0.0001, error="weightKg 须大于 0"),
    )
    grade = fields.Str(required=True, validate=validate.OneOf(["A", "B", "C"]))
    operator_name = fields.Str(required=True, data_key="operatorName", validate=validate.Length(min=1, max=64))


class FlushHarvestOutSchema(Schema):
    id = fields.Int(dump_only=True)
    room_id = fields.Int(data_key="roomId")
    harvested_at = fields.Method("dump_harvested_at", data_key="harvestedAt")
    flush_no = fields.Int(data_key="flushNo")
    weight_kg = fields.Float(data_key="weightKg")
    grade = fields.Str()
    operator_name = fields.Str(data_key="operatorName")

    def dump_harvested_at(self, obj):
        v = obj.harvested_at if hasattr(obj, "harvested_at") else obj["harvested_at"]
        return dt_to_json(v)
