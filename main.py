import asyncio
import os
import cmd

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.mcp import MCPServerStdio
import typer


load_dotenv()

server = MCPServerStdio(
    command='uv', args=['run', 'mcp_ableton_server.py'], env=os.environ
)

ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")

model = OpenAIModel(
    model_name=ollama_model, provider=OpenAIProvider(base_url='http://localhost:11434/v1')
)

agent = Agent(
    model,
    mcp_servers=[server],
)


async def run_chat():
    history = []
    while True:
        async with agent.run_mcp_servers():
            prompt = typer.prompt("Enter your prompt")

            result = await agent.run(prompt, message_history=history)
            history = result.all_messages()

            print(result.data)
            print()


def main():
    asyncio.run(run_chat())


if __name__ == '__main__':
    typer.run(main)
