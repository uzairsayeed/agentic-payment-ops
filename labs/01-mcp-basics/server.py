from mcp.server import MCPServer

mcp = MCPServer("payments-lab")

@mcp.tool()
def get_payment(payment_id: str) -> dict:
    """Retrieve payment details using a payment ID."""
    payments = {
        "PAY-123": {
            "payment_id": "PAY-123",
            "status": "FAILED",
            "amount": 1250,
            "currency": "USD",
            "failure_reason": "INVALID_BENEFICIARY",
        }
    }

    return payments.get(payment_id, {"payment_id": payment_id, "status": "NOT_FOUND",})