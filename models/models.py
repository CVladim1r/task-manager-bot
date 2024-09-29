from tortoise import fields
from tortoise.models import Model
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELED = "canceled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class User(Model):
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True)
    first_name = fields.CharField(max_length=50, null=True)
    last_name = fields.CharField(max_length=50, null=True)

    tasks_created = fields.ReverseRelation["Task"]
    organizations_created = fields.ReverseRelation["Organization"]
    organizations = fields.ManyToManyField("models.Organization", related_name="members", table="user_organization")

    class Meta:
        table = "users"

class Organization(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    created_by = fields.ForeignKeyField("models.User", related_name="organizations_created")
    code = fields.CharField(max_length=10, unique=True)
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

    priority = fields.CharEnumField(enum_type=TaskPriority, default=TaskPriority.MEDIUM)
    status = fields.CharEnumField(enum_type=TaskStatus, default=TaskStatus.PENDING)
    
    completed = fields.BooleanField(default=False)
    reminder_sent = fields.BooleanField(default=False)

    class Meta:
        table = "tasks"
