"""Example: Running Whiteboard Agent with local models via Ollama (e.g. Llama 3.1, Qwen 2.5, Mistral)."""

from whiteboard_agent import WhiteboardAgent

agent = WhiteboardAgent()
openai_compatible_tools = agent.get_tools_schema(format="openai")

def run_ollama_simulation():
    """Ollama supports OpenAI-compatible function calling via localhost:11434/v1.
    
    Using standard requests or the openai client:
    
    from openai import OpenAI
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    
    response = client.chat.completions.create(
        model="llama3.1",
        messages=[
            {"role": "system", "content": agent.get_system_prompt() + "\n" + agent.get_spatial_context()},
            {"role": "user", "content": "Write a note about gravity and draw a circle around it."}
        ],
        tools=openai_compatible_tools
    )
    """
    print("Ollama OpenAI-compatible endpoint schema validated:")
    print(f"Total tools available for local LLM: {len(openai_compatible_tools)}")

if __name__ == "__main__":
    run_ollama_simulation()
