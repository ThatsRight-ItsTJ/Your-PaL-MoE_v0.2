"""
Example demonstrating ultra-simple LLM agent creation with string-based provider specification
Shows the minimal code needed to create and run an AI agent with the new API
"""

import asyncio
import os
import logging
from contextlib import asynccontextmanager

from ..core import new_agent_from_string, new_state


async def main():
    """Main example function"""
    # Check environment variables
    print("Environment check:")
    print(f"OPENAI_API_KEY set: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"AI_API_LIAISON_OPENAI_API_KEY set: {bool(os.getenv('AI_API_LIAISON_OPENAI_API_KEY'))}")
    print(f"ANTHROPIC_API_KEY set: {bool(os.getenv('ANTHROPIC_API_KEY'))}")
    print(f"AI_API_LIAISON_ANTHROPIC_API_KEY set: {bool(os.getenv('AI_API_LIAISON_ANTHROPIC_API_KEY'))}")
    print(f"GEMINI_API_KEY set: {bool(os.getenv('GEMINI_API_KEY'))}")
    print(f"AI_API_LIAISON_GEMINI_API_KEY set: {bool(os.getenv('AI_API_LIAISON_GEMINI_API_KEY'))}")
    print()
    
    # Example 1: Create agent with explicit provider/model
    # Using gpt-4o-mini which is faster and cheaper
    agent1 = None
    try:
        agent1 = await new_agent_from_string("assistant", "openai/gpt-4o-mini")
    except Exception as e:
        # Will suggest setting OPENAI_API_KEY or AI_API_LIAISON_OPENAI_API_KEY
        logging.error(f"Failed to create OpenAI agent: {e}")
    
    # Example 2: Create agent with alias (ultra-simple!)
    try:
        agent2 = await new_agent_from_string("claude-agent", "claude")
        logging.info(f"Created Claude agent: {agent2.name()}")
    except Exception as e:
        logging.error(f"Failed to create Claude agent: {e}")
    
    # Example 3: Create agent with model inference
    try:
        agent3 = await new_agent_from_string("gemini-agent", "gemini-2.0-flash")
        logging.info(f"Created Gemini agent: {agent3.name()}")
    except Exception as e:
        logging.error(f"Failed to create Gemini agent: {e}")
    
    # Example 4: Mock provider for testing (always works)
    try:
        mock_agent = await new_agent_from_string("test-agent", "mock")
    except Exception as e:
        logging.error(f"Failed to create mock agent: {e}")
        return
    
    # Run a simple task
    if agent1:
        try:
            # Using the new state-based interface with timeout
            state = new_state()
            state.set("user_input", "What is 2+2?")
            
            # Run with timeout
            result_state = await asyncio.wait_for(agent1.run(state), timeout=30.0)
            
            output, exists = result_state.get("output")
            if exists:
                print(f"Agent1 response: {output}")
        except asyncio.TimeoutError:
            logging.error("Agent1 timed out")
        except Exception as e:
            logging.error(f"Agent1 error: {e}")
    
    # Using the new state-based interface with mock agent
    try:
        state = new_state()
        state.set("user_input", "Tell me a short joke")
        
        result_state = await mock_agent.run(state)
        
        joke, exists = result_state.get("output")
        if exists:
            print(f"Mock agent joke: {joke}")
    except Exception as e:
        logging.error(f"Mock agent error: {e}")
    
    # Demonstrate the simplicity
    print("\n--- Ultra-Simple Agent Creation Examples ---")
    print('await new_agent_from_string("my-agent", "gpt-4")')
    print('await new_agent_from_string("my-agent", "claude")')
    print('await new_agent_from_string("my-agent", "gemini")')
    print('await new_agent_from_string("my-agent", "openai/gpt-4o-mini")')
    print('await new_agent_from_string("my-agent", "anthropic/claude-3-opus-latest")')
    print('await new_agent_from_string("my-agent", "gemini/gemini-2.0-flash")')


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the example
    asyncio.run(main())