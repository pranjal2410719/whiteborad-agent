"""Tests for LLM tool schema generation and adapters (OpenAI, Anthropic, Gemini, MCP)."""

from whiteboard_agent.agent import WhiteboardAgent


def test_schema_exports():
    agent = WhiteboardAgent()

    # OpenAI format
    openai_tools = agent.get_tools_schema(format="openai")
    assert len(openai_tools) >= 20
    first_oa = openai_tools[0]
    assert first_oa["type"] == "function"
    assert "name" in first_oa["function"]
    assert "parameters" in first_oa["function"]

    # Anthropic format
    anthropic_tools = agent.get_tools_schema(format="anthropic")
    assert len(anthropic_tools) >= 20
    first_ant = anthropic_tools[0]
    assert "name" in first_ant
    assert "input_schema" in first_ant

    # Gemini format
    gemini_tools = agent.get_tools_schema(format="gemini")
    assert len(gemini_tools) >= 20
    first_gem = gemini_tools[0]
    assert "name" in first_gem
    assert "parameters" in first_gem

    # MCP format
    mcp_tools = agent.get_tools_schema(format="mcp")
    assert len(mcp_tools) >= 20
    first_mcp = mcp_tools[0]
    assert "inputSchema" in first_mcp


def test_agent_tool_execution_and_spatial_context():
    agent = WhiteboardAgent()

    # System prompt exists
    prompt = agent.get_system_prompt()
    assert "Whiteboard AI Agent" in prompt

    # Initial spatial context is empty
    ctx = agent.get_spatial_context()
    assert "Clean empty canvas" in ctx

    # Execute tool
    res = agent.execute_tool("create_sticky_note", {"content": "Physics is awesome", "title": "Note"})
    assert res["success"] is True

    # Spatial context now lists element
    updated_ctx = agent.get_spatial_context()
    assert res["id"] in updated_ctx
    assert "Physics is awesome" in updated_ctx
