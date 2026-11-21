from dotenv import load_dotenv
import anthropic
from tools import run_tool
from usage import track

load_dotenv()
client = anthropic.Anthropic(max_retries=4, timeout=60.0)

MAX_STEPS = 8


def get_text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


def run_agent(task: str, system_prompt: str, tools: list, model: str,
              max_steps: int = MAX_STEPS) -> str:
    messages = [{"role": "user", "content": task}]

    for step in range(1, max_steps + 1):
        if step == max_steps and step > 1:
            messages[-1]["content"].append({
                "type": "text",
                "text": "This is your final step. Do not call any tools. "
                        "Write your final answer now using what you have.",
            })

        response = client.messages.create(
            model=model,
            max_tokens=4000,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )
        track(model, response.usage)
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


def revise_text(draft: str, problems: list[str], shortlist_json: str,
                system_prompt: str, model: str) -> str:
    """One tool-free call: fix specific, automatically detected problems."""
    request = (
        "Below are a source shortlist and a draft briefing written from it.\n\n"
        f"SHORTLIST:\n{shortlist_json}\n\nDRAFT:\n{draft}\n\n"
        "An automated check found these problems:\n- "
        + "\n- ".join(problems)
        + "\n\nRewrite the draft to fix exactly these problems. Keep everything "
          "else, follow the original format and rules, and use only information "
          "in the draft and the shortlist. No tools are available now, and the "
          "articles have already been read. Return only the revised briefing, "
          "starting with '## Overview'."
    )
    response = client.messages.create(
        model=model,
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": request}],
    )
    track(model, response.usage)
    return get_text(response)