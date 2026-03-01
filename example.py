"""
Quick demo: Agent Memory Layer in action.
Run: python example.py (with the API running)
"""
import httpx

BASE = "http://localhost:8000/api/v1"


def demo():
    print("🧠 Agent Memory Layer — Demo\n")

    # 1. Create an agent
    agent = httpx.post(f"{BASE}/agents", json={
        "name": "customer-support-bot",
        "description": "Support agent with persistent customer memory"
    }).json()
    agent_id = agent["id"]
    print(f"✅ Agent created: {agent['name']} ({agent_id})\n")

    # 2. Store some memories (simulating past interactions)
    memories = [
        ("Alice has a platinum subscription since 2023, prefers email contact", "semantic"),
        ("Last session with Alice: she was frustrated about slow response times", "episodic"),
        ("Bob is a free tier user, asked about upgrading to pro last week", "semantic"),
        ("Standard refund procedure: submit ticket, 3-5 business days processing", "procedural"),
    ]
    for content, mtype in memories:
        httpx.post(f"{BASE}/agents/{agent_id}/remember", json={
            "content": content,
            "memory_type": mtype,
        })
    print(f"✅ Stored {len(memories)} memories\n")

    # 3. Simulate a new message from Alice
    user_message = "I have a billing problem with my account"
    print(f"👤 User message: '{user_message}'")

    ctx = httpx.post(f"{BASE}/agents/{agent_id}/inject-context", json={
        "message": user_message,
        "top_k": 3,
        "threshold": 0.6,
    }).json()

    print(f"\n📋 Context injected ({ctx['memories_used']} memories recalled):")
    print("─" * 60)
    print(ctx["context_block"])
    print("─" * 60)
    print("\n💡 Your system prompt now becomes:")
    system_prompt = ctx["context_block"] + "\n\nYou are a helpful support agent. Use the context above to personalize your response."
    print(system_prompt[:300] + "...")
    print("\n✨ Your agent is no longer amnesiac.")


if __name__ == "__main__":
    demo()
