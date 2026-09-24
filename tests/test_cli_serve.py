import health_data_connect.cli as cli


def test_serve_ensures_client_then_starts_upstream_stdio(monkeypatch):
    # Exercise run_server's real body: it must import the upstream MCP instance
    # (whose import registers all tools) and call .run(transport="stdio").
    # Only the final blocking call is stubbed, so a broken import path fails here.
    from google_health_mcp.cli import mcp as upstream_mcp

    calls = []
    monkeypatch.setattr(cli, "ensure_client", lambda: calls.append("ensure"))
    monkeypatch.setattr(upstream_mcp, "run", lambda **kw: calls.append(("serve", kw)))

    rc = cli.main(["serve"])

    assert rc == 0
    assert calls == ["ensure", ("serve", {"transport": "stdio"})]


def test_upstream_import_registers_tools():
    # Importing the upstream cli is what registers the health tools on the shared
    # mcp instance; prove at least the core tools are present so `serve` exposes them.
    import asyncio

    from google_health_mcp.cli import mcp as upstream_mcp

    tools = asyncio.run(upstream_mcp.list_tools())
    names = {t.name for t in tools}
    assert names, "no tools registered on the upstream MCP instance"
    assert "health_get_sleep" in names
