from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

response = client.messages.create(
    model="claude-haiku-5-5",
    # max_tokens=300,
    max_tokens=20,
    # system="You are a concise tech news editor. Answer in plain, friendly English.",
    system="You are a pirate.",
    messages=[
        {"role": "user", "content": "My name is Sam."},
        {"role": "assistant", "content": "Nice to meet you, Sam!"},
        {"role": "user", "content": "What is my name?"},
    ],
)

print(response.content[0].text)
print("---")
print("Input tokens:", response.usage.input_tokens)
print("Output tokens:", response.usage.output_tokens)
print("Stop reason:", response.stop_reason)