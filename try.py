from langchain.agents import create_agent
from langchain_ollama import ChatOllama


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


model = ChatOllama(model="llama3")

agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

response = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "What is the weather in San Francisco?"
            }
        ]
    }
)

print(response)