from dotenv import load_dotenv
import anthropic
from tools import run_tool

load_dotenv()
client = anthropic.Anthropic()

MAX_STEPS = 8


def get_text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


def run_agent(task: str, system_prompt: str, tools: list, model: str,
              max_steps: int = MAX_STEPS) -> str:
    messages = [{"role": "user", "content": task}]

    for step in range(1, max_steps + 1):
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )
        print(f"[step {step}] stop_reason={response.stop_reason}, "
              f"input_tokens={response.usage.input_tokens}")
        print("  blocks:", [b.type for b in response.content])

        if response.stop_reason != "tool_use":
            text = get_text(response)
            if response.stop_reason == "max_tokens":
                text += "\n\n[warning: output was cut off]"
            return text

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  -> {block.name}({block.input})")
                result = run_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
        messages.append({"role": "user", "content": tool_results})

    return "Stopped: reached the step limit without a final answer."