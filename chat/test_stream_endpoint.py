import httpx
# Hay que ir cambiando esto para probar ya que el token se caduca
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg4MTY1NDQ0LCJpYXQiOjE3ODgxNjUxNDQsImp0aSI6ImQ2ZjEyYjE4NDM2MDQzNjQ5NDYzYzVmMzQyYzQ2YWFiIiwidXNlcl9pZCI6IjEifQ.11x7Hheb9B57tZDH4a6JBs1xLVci9LXcse2KxsURe4Q"
CONVERSATION_ID = "4722ec34-5245-4f31-ae06-e8f70e222bae"

url = f"http://localhost:8000/api/chat/conversations/{CONVERSATION_ID}/ask_stream/"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

payload = {"content": "Cuentame un chiste corto"}

with httpx.stream("POST", url, headers=headers, json=payload, timeout=60.0) as response:
    print(f"Status: {response.status_code}\n")
    for line in response.iter_lines():
        if line:
            print(line)