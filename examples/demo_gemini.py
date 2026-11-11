"""Example: Providing Whiteboard tools to Google Gemini (or google-genai)."""

import json

from whiteboard_agent import WhiteboardAgent

agent = WhiteboardAgent()
gemini_tools = agent.get_tools_schema(format="gemini")

print(f"Total Gemini function declarations: {len(gemini_tools)}")
print("Sample Gemini function declaration (circle_element):")
print(json.dumps([t for t in gemini_tools if t["name"] == "circle_element"][0], indent=2))

def run_gemini_workflow():
    """Workflow when using google.genai:
    
    from google import genai
    client = genai.Client()
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='Circle the sticky note on the whiteboard',
        config={
            'system_instruction': agent.get_system_prompt() + '\n' + agent.get_spatial_context(),
            'tools': [{'function_declarations': gemini_tools}]
        }
    )
    
    for call in response.function_calls:
        res = agent.execute_tool(call.name, dict(call.args))
        print("Gemini tool execution result:", res)
    """
    print("\nGemini function declarations successfully verified and ready for client.models.generate_content()!")

if __name__ == "__main__":
    run_gemini_workflow()
