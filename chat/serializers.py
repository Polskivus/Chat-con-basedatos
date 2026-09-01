from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "conversation", "role", "content", "send_at"]
        read_only_fields = ["id", "send_at"]

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "follow_at", "messages"]
        read_only_fields = ["id", "created_at", "follow_at"]

class ConversationListSerializer(serializers.ModelSerializer):
    """Versión ligera sin mensajes anidados, para el listado."""
    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "follow_at"]