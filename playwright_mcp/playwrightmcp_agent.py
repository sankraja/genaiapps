"""Build Agent using Microsoft Agent Framework in Python
# Run this python script
> pip install agent-framework
> python <this-script-path>.py
"""

import asyncio
import os
import sys
import logging

from agent_framework import ChatAgent, MCPStdioTool, MCPStreamableHTTPTool, ToolProtocol
from agent_framework_azure_ai import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Azure AI Foundry Agent Configuration
ENDPOINT = "https://raj-honda-ai-foundry.services.ai.azure.com/api/projects/honda-agent-poc"
MODEL_DEPLOYMENT_NAME = "gpt-4.1-mini"

AGENT_NAME = "mcp-agent"
AGENT_INSTRUCTIONS = "You are an intelligent automation assistant with dual capabilities:\n- Web UI Automation Assistant: capable of navigating websites, taking screenshots, performing diverse UI automation tasks such as clicking, typing, form filling, and others.\n- REST API Automation Assistant: able to execute REST API calls, handle responses, and automate API workflows.\n\nYour responsibilities include executing user instructions accurately, performing relevant UI or API automation actions, and providing clear, concise summaries of all UI automation and REST API executions.\n\nThink carefully step by step about each user request before taking action:\n1. Analyze the user's intent and identify whether the task is UI automation, REST API automation, or both.\n2. Plan the necessary steps to accomplish the task safely and effectively.\n3. Use appropriate tools for navigation, interaction, or API calls.\n4. After execution, generate a helpful summary describing what was automated, including success or encountered issues.\n5. Always provide your thought process in a <thinking> section before presenting the final response.\n\nKeep going until the user’s query is completely resolved, before ending your turn and yielding back to the user. If you’re unsure about any detail, use your tools to find accurate information rather than guessing. \n\nYour output must always include the detailed thought process followed by the final actionable results and summaries. Use raw XML tags for structured output. Preserve all context and variables relevant to the task."



def create_mcp_tools() -> list[ToolProtocol]:
    screenshot_directory = r"c:\\Users\\v0421312\\source\\ams\\AWS Semantic Framework\\simplemaf\\screenshots"
    return [
        MCPStdioTool(
            name="aitk-playwright-example".replace("-", "_"),
            description="MCP server for aitk-playwright-example",
            command="npx",
            args=[
                "-y",
                "@playwright/mcp@latest",
                "--output-dir",
                screenshot_directory
            ]
        ),
    ]

async def main() -> None:
    # Read prompt from stdin if available
    import datetime
    if not sys.stdin.isatty():
        user_input = sys.stdin.read().strip()
        if not user_input:
            user_input = "Hello, agent!"
    else:
        user_input = "Hello, agent!"

    # Generate dynamic screenshot filename with timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    screenshot_filename = f"screenshot_{timestamp}.png"
    # If the user prompt requests a screenshot, append save instruction
    if "screenshot" in user_input.lower():
        user_input += f" (Save screenshot as {screenshot_filename})"
    try:
        async with (
            DefaultAzureCredential() as credential,
            ChatAgent(
                chat_client=AzureAIAgentClient(
                    project_endpoint=ENDPOINT,
                    model_deployment_name=MODEL_DEPLOYMENT_NAME,
                    async_credential=credential,
                    agent_name=AGENT_NAME,
                    agent_id=None,  # Since no Agent ID is provided, the agent will be automatically created and deleted after getting response
                ),
                instructions=AGENT_INSTRUCTIONS,
                tools=create_mcp_tools(),
            ) as agent
        ):
            thread = agent.get_new_thread()
            print(f"\n# User: '{user_input}'")
            try:
                async for chunk in agent.run_stream([user_input], thread=thread):
                    if chunk.text:
                        print(chunk.text, end="")
                    elif (
                        chunk.raw_representation
                        and chunk.raw_representation.raw_representation
                        and hasattr(chunk.raw_representation.raw_representation, "status")
                        and hasattr(chunk.raw_representation.raw_representation, "type")
                        and chunk.raw_representation.raw_representation.status == "completed"
                        and hasattr(chunk.raw_representation.raw_representation, "step_details")
                        and hasattr(chunk.raw_representation.raw_representation.step_details, "tool_calls")
                    ):
                        print("")
                        print("Tool calls: ", chunk.raw_representation.raw_representation.step_details.tool_calls)
            except Exception as agent_exc:
                logging.error(f"Agent run_stream error: {agent_exc}")
                import traceback
                traceback.print_exc()
            print("")
            print("\n--- Task completed successfully ---")
    except Exception as e:
        logging.error(f"Agent main() error: {e}")
        import traceback
        traceback.print_exc()
    await asyncio.sleep(1.0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Program finished.")
