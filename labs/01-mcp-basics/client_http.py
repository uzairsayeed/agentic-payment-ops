import asyncio

from mcp import Client


async def main() -> None:
    async with Client("http://localhost:8000/mcp") as client:

        print("Protocol version:")
        print(client.protocol_version)

        tools = await client.list_tools()

        print("\nAvailable tools:")

        for tool in tools.tools:
            print(f"\nName: {tool.name}")
            print(f"Description: {tool.description}")
            print(f"Input schema: {tool.input_schema}")

        result = await client.call_tool(
            "get_payment",
            {
                "payment_id": "PAY-123",
            },
        )

        print("\nTool result:")
        print(result)

        print("\nStructured content:")
        print(result.structured_content)


asyncio.run(main())