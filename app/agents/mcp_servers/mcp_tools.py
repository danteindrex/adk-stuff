async def mcp_playwright():
    return MCPToolset(
                    connection_params=StdioConnectionParams(
                        command="npx",
                        args=[
                            "-y", 
                            "@modelcontextprotocol/server-playwright@latest"
                        ]
                    )
                )