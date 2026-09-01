import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from chat.models import Conversation, Message
from chat.services.llm_mock import MockLLMCLient

User = get_user_model()


@pytest.mark.django_db
def test_ask_creates_user_and_assistant_messages(monkeypatch):
    user = User.objects.create_user(username="testuser", password="testpass123")
    client = APIClient()
    client.force_authenticate(user=user)

    conversation = Conversation.objects.create(owner=user, title="Test conversation")

    monkeypatch.setattr("chat.views.HttpxLLMClient", lambda: MockLLMCLient())

    response = client.post(
        f"/api/chat/conversations/{conversation.id}/ask/",
        {"content": "Hola"},
        format="json",
    )

    assert response.status_code == 200
    assert "user_message" in response.data
    assert "assistant_message" in response.data
    assert response.data["assistant_message"]["role"] == "assistant"
    assert Message.objects.filter(conversation=conversation, role="user").exists()
    assert Message.objects.filter(conversation=conversation, role="assistant").exists()