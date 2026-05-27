from langchain_core.tools import tool

@tool
def check_stock(sku: str, warehouse: str = None) -> str:
    """dummy so that i can get work done!!"""
    
    return "Dummy stock data: We have 42 in stock."
    