import asyncio
import mcp.server.stdio
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions

from wiki_agent_mcp.server import server
from wiki_agent_mcp.utils.config import init_data_dirs

async def run_server():
    # Initialize directories and logging
    init_data_dirs()
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="wiki-agent-server",
                server_version="2.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

def main():
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
