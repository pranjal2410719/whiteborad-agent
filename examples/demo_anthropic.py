"""Example: Providing Whiteboard tools to Anthropic Claude."""

import json

from whiteboard_agent import WhiteboardAgent

agent = WhiteboardAgent()
anthropic_tools = agent.get_tools_schema(format="anthropic")

print(f"Total Anthropic tools exported: {len(anthropic_tools)}")
print("Sample tool schema (create_formula):")
print(json.dumps([t for t in anthropic_tools if t["name"] == "create_formula"][0], indent=2))

def run_anthropic_workflow():
    """Workflow when using Anthropic Python SDK:
    
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=agent.get_system_prompt() + "\n" + agent.get_spatial_context(),
        messages=[{"role": "user", "content": "Draw an architecture diagram for our whiteboard agent"}],
        tools=anthropic_tools
    )
    
    for block in response.content:
        if block.type == "tool_use":
            res = agent.execute_tool(block.name, block.input)
            print("Tool result:", res)
    """
    print("\nAnthropic workflow schema verified and ready for client.messages.create()!")

if __name__ == "__main__":
    run_anthropic_workflow()
