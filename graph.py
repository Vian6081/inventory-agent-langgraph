from typing import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from langgraph.graph import START, END , StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

# 1. Importing all tools 
from tools import check_stock, list_items, summarise_inventory, update_stock, delete_item

# 2. The Agent State Prompt
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    missing_ent : list[str]

sys_prompt = """You are an AI Inventory Management Assistant connected to a live SQLite database.

### CORE WORKFLOW
1. You MUST use the provided tools to fetch or modify real data. NEVER make up or guess inventory numbers.
2. READ ACTIONS:
   - `check_stock`: Use when the user asks about a specific SKU.
   - `list_items`: Use to filter items by category or warehouse.
   - `summarise_inventory`: Use for high-level overviews. (Valid scopes: 'by_warehouse', 'by_category', 'total').
3. WRITE/DELETE ACTIONS:
   - `update_stock`: Use to add or deduct stock (use positive/negative numbers).
   - `delete_item`: Use ONLY when the user explicitly requests to remove a SKU.

### HANDLING AMBIGUITY
- If a user's query is at all ambiguous (e.g., missing a specific SKU or warehouse), you must NOT guess.
- Instead of calling a tool, output a standard conversational reply asking the user to clarify. 

"""
# 3. Iniliazing LLM

llm = ChatOllama(model ="llama3.1")

tools_list = [check_stock, list_items, summarise_inventory, update_stock, delete_item]
llm_with_tool = llm.bind_tools(tools_list)
tool_node= ToolNode(tools_list)

# 4.The Agent Node
def agent (state: AgentState):
    system_message = {"role":"system","content":sys_prompt}
    messages_with_system = [system_message] + state["messages"]
    
    # LLM reads history and decides output
    response = llm_with_tool.invoke(messages_with_system) 
    return {"messages" : [response]}

# 5. Building the Graph
workflow = StateGraph(AgentState)
workflow.add_node("agent",agent)
workflow.add_node("tools",tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent",tools_condition)
workflow.add_edge("tools","agent")

graph = workflow.compile()
<<<<<<< HEAD
def ask_inventory_agent(user_input):
    initial_state = {"messages":[("user",user_input)]}
    result = graph.invoke(initial_state)
    return result["messages"][-1].content
=======

# 6.The Execution Loop 
print("\n🤖 AI Inventory Agent Initialized. Type 'quit' to exit.")

while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Shutting down...")
        break
    
    # We pass the user's message into the graph using the AgentState blueprint
    initial_state = {"messages": [("user", user_input)]}
    
    # Stream the graph's execution
    events = graph.stream(initial_state, stream_mode="values")
    
    for event in events:
        # Grab the most recent message from the state
        recent_message = event["messages"][-1]
        
        # We only want to print the AI's or Tool's responses, not echo our own input
        if recent_message.type != "human":
            print(f"\n[{recent_message.type.upper()}]: {recent_message.content}")



>>>>>>> 533a7e74952047445fc3b8cb7d89095c5b1d52c3
