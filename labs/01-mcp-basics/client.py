import asyncio

from mcp import Client, StdioServerParameters

async def main() -> None:
    # Equivalent terminal command: uv run mcp run server.py
    # Creating stdio server
    server = StdioServerParameters(
        command = "uv",
        args = [
            'run',
            'mcp',
            'run',
            'server.py'
        ]
    )

    # Creating an MCP client connected to the above stdio server.
    async with Client(server) as client:
        tools = await client.list_tools()

        print('Available tools: ')

        for tool in tools.tools:
            print(f'- {tool.name}')
            print(f'- Description: {tool.description}')
            print(f'- Input schema: {tool.input_schema}')

        result = await client.call_tool(
            'get_payment',
            {
                'payment_idx': 'PAY-1234'
            }
        )

        print("\nTool result:", result)
        print('\n', result.structured_content)

asyncio.run(main())
