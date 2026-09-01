import asyncio
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chat.models import Conversation, Message
from chat.services.llm import HttpxLLMClient

User = get_user_model()

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--user", type=str, default="admin")

    def handle(self, *args, **options):
        username = options["user"]
        user = User.objects.get(username=username)

        conversation = Conversation.objects.create(owner=user, title="Streaming x consola")
        self.stdout.write(self.style.SUCCESS(f"Conversacion creada: {conversation.id}"))
        self.stdout.write("Escribe aqui tus preguntas, escribe 'salir' para terminar el chat:\n")

        while True:
            user_input = input("Tu: ")
            if user_input.lower() in ("salir", "exit", "quit"):
                break

            Message.objects.create(conversation=conversation, role="user", content=user_input)

            history = [
                {"role": m.role, "content": m.content}
                for m in conversation.messages.all()
            ]

            print("Asistente: ", end="", flush=True)
            full_response = asyncio.run(self._stream_and_print(history))
            print()

            Message.objects.create(conversation=conversation, role="assistant", content=full_response)

        self.stdout.write(self.style.SUCCESS("Conversacion guardada."))

    async def _stream_and_print(self, history):
        client= HttpxLLMClient()
        chunks = []
        async for chunk in client.stream_complete(history):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
        await client.aclose()
        return "".join(chunks)