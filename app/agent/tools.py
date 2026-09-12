async def get_user_profile() -> dict:
    return {
        "name": "Demo User",
    }


async def get_portfolio() -> dict:
    return {
        "value": 100_000_000,
        "currency": "VND",
    }


async def get_order_status(
    order_id: str,
) -> dict:
    return {
        "order_id": order_id,
        "status": "unknown",
    }


TOOLS: list[dict] = []
