from mcp.server.fastmcp import FastMCP

mcp = FastMCP("test")

@mcp.tool()
def add_item_to_cart(name: str, quantity: int) -> dict:
    """
    Adds a specific quantity of a food item to the user's shopping cart. 
    Use this when the user wants to add something new to their order.
    Example: If the user says 'add 2 pizzas', the arguments should be name='pizza' and quantity=2.
    """
    return {"action" : "add", "item_name": name, "quantity": quantity}

@mcp.tool()
def remove_item_from_cart(name: str) -> dict:
    """
    Removes ALL units of a specific food item from the shopping cart.
    Use this when the user wants to cancel or completely remove an existing item.
    Example: If the user says 'remove the sodas', the argument should be name='soda'.
    """
    return {"action" : "remove", "item_name": name}

@mcp.tool()
def replace_item_in_cart(old_item_name: str, new_item_name: str, new_item_quantity: int) -> dict:
    """
    Replaces an existing item in the cart with a new item and quantity. 
    Use this specifically when a user wants to SWAP or CHANGE one item for another. This tool is better than using remove and then add.
    Example: If a user says 'instead of pizza, I want 2 cokes', the arguments must be old_item_name='pizza', new_item_name='coke', and new_item_quantity=2.
    """
    return {
        "action": "replace",
        "item_to_remove": old_item_name,
        "item_to_add": {
            "name": new_item_name,
            "quantity": new_item_quantity
        }
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
