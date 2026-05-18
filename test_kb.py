#!/usr/bin/env python3
"""
Test script for the AI Ops Copilot knowledge base
"""

from knowledge.knowledge_base import KnowledgeBase

def main():
    print("Testing Knowledge Base...")
    kb = KnowledgeBase()
    incidents = kb.get_all_incidents()
    print(f"Loaded {len(incidents)} incidents")

    if incidents:
        print("Sample incidents:")
        for inc in incidents[:3]:
            print(f"  - {inc['id']}: {inc['system']} ({inc['severity']})")

    # Test similarity search
    test_query = "SFTP connection failure"
    print(f"\nTesting similarity search for: '{test_query}'")
    import asyncio
    similar = asyncio.run(kb.find_similar_incidents(test_query, limit=2))
    for inc in similar:
        print(f"  - {inc['id']}: {inc['similarity_score']:.2f}")

if __name__ == "__main__":
    main()