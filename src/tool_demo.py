import json
from dotenv import load_dotenv
import anthropic
from tools import fetch_all_recent

load_dotenv()
client = anthropic.Anthropic()

def get_text(response) -> str:
    """Join all text blocks in a response, ignoring thinking and tool blocks."""
    return "".join(b.text for b in response.content if b.type == "text")

TOOLS = [
    {
        "name": "fetch_recent_ai_news",
        "description": (
            "Fetch AI news articles published recently from major tech blogs and "
            "news sites (TechCrunch, The Verge, MIT Technology Review, OpenAI, "
            "Hugging Face). Returns a list of items, each with source, title, "
            "link, published time, and a short summary."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "How many hours back to look. Defaults to 24.",
                    "minimum": 1,
                    "maximum": 72,
                }
            },
            "required": [],
        },
    }
]

messages = [
    {"role": "user", "content": "What happened in AI in the last 24 hours?"}
]
# messages = [
#     {"role": "user", "content": "Gets news"}
# ]

# --- Round 1: Claude decides whether to use the tool ---
response = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=1500,
    tools=TOOLS,
    messages=messages,
)

print("Stop reason:", response.stop_reason)
for block in response.content:
    print("Block type:", block.type)
    if block.type == "tool_use":
        print("  Tool requested:", block.name)
        print("  With input:", block.input)

if response.stop_reason != "tool_use":
    print(get_text(response))
    raise SystemExit

# --- Your code runs the tool ---
tool_use = next(b for b in response.content if b.type == "tool_use")
result = fetch_all_recent(**tool_use.input)
print(f"\nTool returned {len(result)} items\n")

# --- Round 2: send the result back ---
messages.append({"role": "assistant", "content": response.content})
messages.append({
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": tool_use.id,
        "content": json.dumps(result),
    }],
})

final = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=1500,
    tools=TOOLS,
    messages=messages,
)

print("Stop reason:", final.stop_reason)
print(get_text(final))
print("\nInput tokens:", final.usage.input_tokens)
print("Output tokens:", final.usage.output_tokens)