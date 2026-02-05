"""Quick delegation test - Does epistemic-architect actually use invoke_agent?

Run this to test if the agent can delegate:
    python3 scripts/test_delegation_live.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from code_puppy.agents.agent_epistemic_architect import EpistemicArchitectAgent
from pydantic_ai.models import ModelSettings

async def test_delegation():
    print("=" * 70)
    print("LIVE DELEGATION TEST")
    print("=" * 70)
    
    architect = EpistemicArchitectAgent()
    
    # Simple prompt that SHOULD trigger delegation
    test_prompt = """
I need you to analyze the security of the file code_puppy/core/failover_config.py.

This is a test to verify OODA delegation works. You should:
1. OBSERVE: Read the file yourself
2. ORIENT: Delegate security analysis to security-auditor agent
3. DECIDE: Should we make changes?
4. ACT: If changes needed, explain what

Make sure you use invoke_agent for the security audit!
"""
    
    print("\n📝 Test Prompt:")
    print(test_prompt)
    print("\n🔄 Running epistemic-architect...")
    print("-" * 70)
    
    try:
        # Create a simple agent instance
        from pydantic_ai import Agent
        from code_puppy.model_factory import ModelFactory
        
        models_config = ModelFactory.load_config()
        model = ModelFactory.get_model("synthetic-Kimi-K2.5-Thinking", models_config)
        
        # Register tools
        from code_puppy.tools import agent_tools
        
        agent = Agent(
            model=model,
            instructions=architect.get_system_prompt(),
            output_type=str,
        )
        
        # Register invoke_agent
        agent_tools.register_invoke_agent(agent)
        
        # Run with streaming to see tool calls
        print("\n⚡ Streaming response...")
        result = await agent.run(test_prompt)
        
        print("\n" + "=" * 70)
        print("RESULT:")
        print("=" * 70)
        print(result.output)
        
        # Check if invoke_agent was called
        print("\n" + "=" * 70)
        print("TOOL USAGE ANALYSIS:")
        print("=" * 70)
        
        tool_calls = []
        for msg in result.all_messages():
            for part in getattr(msg, 'parts', []):
                if hasattr(part, 'tool_name'):
                    tool_calls.append(part.tool_name)
        
        if tool_calls:
            print(f"✅ Tools called: {', '.join(set(tool_calls))}")
            if 'invoke_agent' in tool_calls:
                print("🎯 SUCCESS: invoke_agent was used!")
            else:
                print("⚠️  WARNING: invoke_agent not used, only: " + ', '.join(set(tool_calls)))
        else:
            print("❌ FAILURE: No tools were called at all")
            print("\nPossible reasons:")
            print("   1. Model doesn't recognize when to use tools")
            print("   2. Prompt too vague or doesn't match delegation patterns")
            print("   3. Model trying to answer directly without delegation")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_delegation())
