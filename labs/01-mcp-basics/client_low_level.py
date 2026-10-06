import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server_params = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "mcp",
            "run",
            "server.py",
        ],
    )

    # stdio_client() essentially does two jobs.
        # 1. Launch server.py
        # 2. connect pipes
    #                    MCP messages
    # client write ───────────────────► server stdin
    # client read  ◄─────────────────── server stdout
    async with stdio_client(server_params) as (read, write):

        # We are creating the MCP protocol session on top of those transport streams.
        async with ClientSession(read, write) as session:

            # This establishes the MCP relationship between this client and the server before normal operations such as tool discovery.
            await session.initialize()

            tools = await session.list_tools()

            print("\nAvailable tools:")

            for tool in tools.tools:
                print(f"\nName: {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Input schema: {tool.input_schema}")

            result = await session.call_tool(
                "get_payment",
                arguments={
                    "payment_id": "PAY-123",
                },
            )

            print("\nTool result:")
            print(result)

            print("\nStructured content:")
            print(result.structured_content)


asyncio.run(main())