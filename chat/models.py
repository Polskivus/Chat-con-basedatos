from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid

# Create your models here.
class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    follow_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-follow_at"]

class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    send_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["send_at"]

class UsageLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usage_logs")
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    prompt_tokens = models.PositiveIntegerField()
    completion_tokens = models.PositiveIntegerField()
    estimated_cost_usd = models.DecimalField(max_digits=10, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]