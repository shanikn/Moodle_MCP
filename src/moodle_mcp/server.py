from mcp.server.mcpserver import MCPServer

mcp = MCPServer("notability")

@mcp.tool()
def hello(name: str) -> str:
    """Greet a person by name. Returns a greeting string"""
    return f'Hello, {name}.'

if __name__ == "__main__":
    mcp.run()