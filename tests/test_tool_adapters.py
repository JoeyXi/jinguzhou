from jinguzhou.tools.adapters import ToolAdapterConfig, ToolAdapterRegistry


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
    assert tool_calls[0].extraction.path_fields[-1] == "location"
    assert "statement_text" in tool_calls[2].extraction.sql_fields
