"""ESP32 MicroPython Dev Station — MCP server entry point."""
# Implementation in Plan 04 (01-04-PLAN.md)
# This stub allows imports to resolve during test collection.
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("esp32-station")

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
