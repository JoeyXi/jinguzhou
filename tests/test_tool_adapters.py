from jinguzhou.adapters import NormalizedToolCall, ToolAdapterConfig, ToolAdapterRegistry


def test_registry_resolves_custom_adapter_before_defaults() -> None:
    registry = ToolAdapterRegistry.with_defaults(
        [
            ToolAdapterConfig(
                name="custom-filesystem",
                protocols=["openai"],
                tool_name_patterns=["filesystem.write"],
                priority=500,
            )
        ]
    )

    adapter = registry.resolve("openai", "filesystem.write")

    assert adapter.name == "custom-filesystem"


def test_registry_extracts_multiple_protocol_shapes() -> None:
    registry = ToolAdapterRegistry.with_defaults()
    response_payload = {
        "choices": [
            {
                "message": {
                    "tool_calls": [
                        {
                            "id": "openai_1",
                            "type": "function",
                            "function": {"name": "filesystem.write", "arguments": '{"target":"/etc/hosts"}'},
                        }
                    ]
                }
            },
            {
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "mcp_1",
                            "name": "mcp.filesystem.read_file",
                            "input": {"location": "/Users/jx/.ssh/id_rsa"},
                        }
                    ]
                }
            },
            {
                "message": {
                    "additional_kwargs": {
                        "tool_calls": [
                            {
                                "id": "lc_1",
                                "name": "db.run_sql",
                                "args": {"statement_text": "DROP TABLE users"},
                            }
                        ]
                    }
                }
            },
        ]
    }

    tool_calls = registry.extract_tool_calls(response_payload)

    assert [tool_call.protocol for tool_call in tool_calls] == ["openai", "mcp", "langchain"]
    assert [tool_call.adapter_name for tool_call in tool_calls] == ["filesystem-write", "filesystem-read", "database"]
    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "filesystem.write",
        "filesystem.read",
        "database.query",
    ]
    assert "location" in tool_calls[0].extraction.path_fields
    assert "statement_text" in tool_calls[2].extraction.sql_fields


def test_registry_normalizes_direct_tool_call() -> None:
    registry = ToolAdapterRegistry.with_defaults()

    tool_call = registry.normalize_tool_call(
        protocol="llamaindex",
        tool_name="filesystem.write",
        arguments={"path": "/etc/hosts"},
        id="llama_1",
        type="tool_call",
        metadata={"agent": "demo"},
    )

    assert isinstance(tool_call, NormalizedToolCall)
    assert tool_call.id == "llama_1"
    assert tool_call.protocol == "llamaindex"
    assert tool_call.tool_name == "filesystem.write"
    assert tool_call.arguments == {"path": "/etc/hosts"}
    assert tool_call.metadata["agent"] == "demo"


def test_registry_extracts_agent_ecosystem_protocol_shapes() -> None:
    registry = ToolAdapterRegistry.with_defaults()

    mcp_calls = registry.extract_tool_calls(
        {
            "jsonrpc": "2.0",
            "id": "mcp_call_1",
            "method": "tools/call",
            "params": {
                "name": "mcp.fetch.get",
                "arguments": {"request": {"url": "https://demo.ngrok.io/collect"}},
            },
        }
    )
    openai_agent_calls = registry.extract_tool_calls(
        {
            "output": [
                {
                    "type": "function_call",
                    "call_id": "agent_call_1",
                    "name": "db.run_sql",
                    "arguments": '{"sql":"DROP TABLE users"}',
                }
            ]
        }
    )
    llamaindex_calls = registry.extract_tool_calls(
        {
            "framework": "llamaindex",
            "tool_calls": [
                {
                    "id": "li_1",
                    "tool_name": "filesystem.write",
                    "kwargs": {"operations": [{"target": "/tmp/a"}, {"target": "/etc/hosts"}]},
                }
            ],
        }
    )

    assert mcp_calls[0].protocol == "mcp"
    assert mcp_calls[0].tool_name == "network.request"
    assert openai_agent_calls[0].protocol == "openai_agents"
    assert openai_agent_calls[0].tool_name == "database.query"
    assert llamaindex_calls[0].protocol == "llamaindex"
    assert llamaindex_calls[0].tool_name == "filesystem.write"
