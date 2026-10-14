"""Opt-in LOCAL MCP tools for Claude Desktop / compatible agents.

To install: pip install -r requirements-mcp.txt
To launch through STDIO: python -m service.mcp_server
The MCP server can retrieve only explicitly persisted reports; it does not receive
host microphone audio. Deploying remote MCP requires proper user auth and tenancy.
"""
from .store import ReportStore


def read_report(rehearsal_id: str) -> dict:
    result = ReportStore().get(rehearsal_id)
    if result is None:
        return {"error": "No stored report with this ID (or it expired)."}
    return result


def read_events(rehearsal_id: str) -> dict:
    report = read_report(rehearsal_id)
    return {"events": report.get("events", []), "error": report.get("error")} if "error" in report else {"events": report.get("events", [])}


def make_practice_plan(rehearsal_id: str) -> dict:
    report = read_report(rehearsal_id)
    if "error" in report:
        return report
    return {"goal": report.get("goal", ""),
            "suggestions": report.get("suggestions", []),
            "structure": report.get("pitch_structure", []),
            "disclaimer": "Suggestions are heuristic and require the speaker's judgment."}


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise SystemExit("Install optional MCP SDK: pip install -r requirements-mcp.txt") from exc
    server = FastMCP("SpeechTrace Local Reports")
    server.tool()(read_report)
    server.tool()(read_events)
    server.tool()(make_practice_plan)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
