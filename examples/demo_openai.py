"""Example: Driving WhiteboardAgent using OpenAI (or OpenAI-compatible API e.g. OpenRouter/vLLM)."""

import json
import os

from whiteboard_agent import WhiteboardAgent

# Setup agent
agent = WhiteboardAgent()
tools_schema = agent.get_tools_schema(format="openai")

PROMPT = "Draw the Pythagorean theorem on the whiteboard, underline the formula, and add a sticky note with an example 3-4-5 triangle."

def mock_llm_or_openai_run():
    """Demonstrates how to pass tools to OpenAI and loop tool execution."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Note: OPENAI_API_KEY not set. Simulating what OpenAI tool calls look like:")
        # Simulated sequence of OpenAI tool call responses
        simulated_calls = [
            ("create_formula", {"title": "Pythagoras Theorem", "formula": "a² + b² = c²", "steps": ["a, b are legs", "c is hypotenuse"]}),
            ("underline_element", {"target_id": "WILL_USE_LAST_ID", "color": "#e11d48"}),
            ("create_sticky_note", {"title": "Classic Triplet", "content": "3² + 4² = 9 + 16 = 25 = 5²", "color": "green", "direction": "right"}),
        ]
        last_id = None
        for fn_name, args in simulated_calls:
            if args.get("target_id") == "WILL_USE_LAST_ID":
                args["target_id"] = last_id
            print(f"\n[OpenAI Tool Call] {fn_name}({args})")
            res = agent.execute_tool(fn_name, args)
            last_id = res.get("id")
            print(f" -> Result: {res['message']}")
        return

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    messages = [
        {"role": "system", "content": agent.get_system_prompt() + "\n" + agent.get_spatial_context()},
        {"role": "user", "content": PROMPT},
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools_schema,
        tool_choice="auto",
    )

    response_msg = response.choices[0].message
    if response_msg.tool_calls:
        for tool_call in response_msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"Executing LLM Tool: {name} with args {args}")
            res = agent.execute_tool(name, args)
            print(f"Result: {res}")

if __name__ == "__main__":
    mock_llm_or_openai_run()
    print("\nFinal Spatial Context:")
    print(agent.get_spatial_context())
