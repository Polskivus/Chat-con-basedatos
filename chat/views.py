import json
from decimal import Decimal
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from django.http import StreamingHttpResponse
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from .models import Conversation, Message, UsageLog
from .serializers import ConversationSerializer, ConversationListSerializer, MessageSerializer
from .services.llm import HttpxLLMClient

PRICE_PER_1K_PROMPT = Decimal("0.0005")
PRICE_PER_1K_COMPLETION = Decimal("0.0015")

def _calculate_cost(prompt_tokens: int, completion_tokens: int) -> Decimal:
    return (
        Decimal(prompt_tokens) / 1000 * PRICE_PER_1K_PROMPT
        + Decimal(completion_tokens) / 1000 * PRICE_PER_1K_COMPLETION
    )

async def _ask_llm(llm_client, history):
    respuesta = await llm_client.complete(history)
    await llm_client.aclose()
    return respuesta

async def _sse_stream(llm_client, history, conversation):
    full_response = []
    async for chunk in llm_client.stream_complete(history):
        full_response.append(chunk)
        yield f"data: {json.dumps({'delta': chunk})}\n\n"

    await llm_client.aclose()

    assistant_content = "".join(full_response)
    await Message.objects.acreate(
        conversation=conversation, role="assistant", content=assistant_content
    )

    yield f"data: {json.dumps({'done': True})}\n\n"

@method_decorator(ratelimit(key="user", rate="10/m", block=True), name="ask")
class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        # cada usuario solo ve sus propias conversaciones
        return Conversation.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ConversationListSerializer
        return ConversationSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def ask(self, request, pk=None):
        conversation = self.get_object()
        user_content = request.data.get("content", "")

        if not user_content:
            return Response({"error": "El campo 'content' es obligatorio"}, status=400)

        user_msg = Message.objects.create(
            conversation=conversation, role="user", content=user_content
        )

        history = [
            {"role": m.role, "content": m.content}
            for m in conversation.messages.all()
        ]
        llm_client = HttpxLLMClient()
        respuesta = async_to_sync(_ask_llm)(llm_client, history) # Aqui mandamos la pregunta y recogemos la respuesta del LLM

        assistant_msg = Message.objects.create(
            conversation=conversation, role="assistant", content=respuesta["content"]
        )

        async_to_sync(llm_client.aclose)() # Aqui cerramos la conxion

        usage = respuesta["usage"]
        UsageLog.objects.create(
            user=request.user,
            conversation=conversation,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            estimated_cost_usd=_calculate_cost(usage["prompt_tokens"], usage["completion_tokens"]),
        )

        return Response({
            "user_message": MessageSerializer(user_msg).data,
            "assistant_message": MessageSerializer(assistant_msg).data,
        })

    @action(detail=True, methods=["post"])
    def ask_stream(self, request, pk=None):
        conversation = self.get_object()
        user_content = request.data.get("content", "")

        if not user_content:
            return Response({"error": "El campo 'content' es obligatorio"}, status=400)

        Message.objects.create(conversation=conversation, role="user", content=user_content)

        history = [
            {"role": m.role, "content": m.content}
            for m in conversation.messages.all()
        ]

        llm_client = HttpxLLMClient()

        response = StreamingHttpResponse(
            _sse_stream(llm_client, history, conversation),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

class MessageViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        return Message.objects.filter(conversation__owner=self.request.user)