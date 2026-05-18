#!/usr/bin/env python3
"""
AI Ops Copilot System Runner
Demonstrates the incident management workflow
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agents.l1_triage_agent import L1TriageAgent
from agents.base_agent import AgentInput
from knowledge.knowledge_base import KnowledgeBase


async def main():
    """Main function to run the AI Ops Copilot demo"""

    print("🤖 AI Ops Copilot System")
    print("=" * 50)

    # Initialize knowledge base
    print("📚 Initializing Knowledge Base...")
    kb = KnowledgeBase()

    # Initialize L1 Triage Agent
    print("🔍 Initializing L1 Triage Agent...")
    l1_agent = L1TriageAgent(kb)

    # Sample incident data
    sample_incident = {
        "title": "SFTP Connection Failure",
        "description": """
        We have multiple Dmaap jobs aborting with the following error:
        Cannot connect to the SFTP server 10.59.2.4
        The die message: Cannot connect to the SFTP server
        This is affecting data ingestion from multiple sources.
        """
    }

    print("\n🚨 Processing Sample Incident:")
    print(f"Title: {sample_incident['title']}")
    print(f"Description: {sample_incident['description'][:100]}...")

    # Create agent input
    input_data = AgentInput(
        incident_id="INC_TEST_001",
        data=sample_incident
    )

    # Process through L1 agent
    print("\n⚙️  Running L1 Triage Analysis...")
    result = await l1_agent.process(input_data)

    # Display results
    print("\n📊 L1 Analysis Results:")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Needs Escalation: {result.result['needs_escalation']}")

    classification = result.result['classification']
    print("\n🏷️  Classification:")
    print(f"  System: {classification['system']}")
    print(f"  Type: {classification['incident_type']}")
    print(f"  Severity: {classification['severity']}")
    print(f"  Components: {', '.join(classification['affected_components'])}")

    similar = result.result['similar_incidents']
    print("\n🔍 Similar Incidents:")
    if similar:
        for inc in similar[:3]:
            print(f"  {inc['id']} (similarity: {inc['similarity_score']:.2f})")
    else:
        print("  No similar incidents found")

    fixes = result.result['quick_fixes']
    print("\n🔧 Suggested Quick Fixes:")
    if fixes:
        for i, fix in enumerate(fixes, 1):
            print(f"  {i}. {fix['description']}")
            print(f"     Estimated time: {fix['estimated_time']}")
    else:
        print("  No quick fixes available")

    correlations = result.result['correlations']
    print("\n🔗 Correlated Incidents:")
    if correlations:
        print(f"  {', '.join(correlations)}")
    else:
        print("  No correlated incidents found")

    if result.result['needs_escalation']:
        print("\n⚠️  Escalation Reason:")
        print(f"  {result.result['escalation_reason']}")

    print("\n💡 Recommendations:")
    for rec in result.recommendations:
        print(f"  • {rec}")

    print("\n✅ L1 Processing Complete!")
    print("Next steps would involve L2 Analysis Agent if escalated.")


if __name__ == "__main__":
    asyncio.run(main())