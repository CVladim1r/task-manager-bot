from tortoise import fields
from tortoise.models import Model

class User(Model):
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True)
    first_name = fields.CharField(max_length=50, null=True)
    last_name = fields.CharField(max_length=50, null=True)

    tasks_created = fields.ReverseRelation["Task"]
    organizations_created = fields.ReverseRelation["Organization"]

    class Meta:
        table = "users"


class Organization(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    created_by = fields.ForeignKeyField("models.User", related_name="organizations_created")
    
    tasks = fields.ReverseRelation["Task"]

    class Meta:
        table = "organizations"


class Task(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    deadline = fields.DatetimeField()
    reminder_time = fields.DatetimeField()
    created_by = fields.ForeignKeyField("models.User", related_name="tasks_created")
    organization = fields.ForeignKeyField("models.Organization", related_name="tasks", null=True)
    assigned_users = fields.ManyToManyField("models.User", related_name="tasks_assigned")
    completed = fields.BooleanField(default=False)
    reminder_sent = fields.BooleanField(default=False)

    class Meta:
        table = "tasks"