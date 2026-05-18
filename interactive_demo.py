#!/usr/bin/env python3
"""
Interactive CLI Demo for AI Ops Copilot
Allows users to input incidents and see AI analysis
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agents.l1_triage_agent import L1TriageAgent
from agents.base_agent import AgentInput
from knowledge.knowledge_base import KnowledgeBase


def print_banner():
    """Print the application banner"""
    print("""
🤖 AI Ops Copilot - Incident Management System
═══════════════════════════════════════════════

This system helps AO and AM teams resolve incidents faster by:
• Automatically classifying incidents
• Finding similar historical cases
• Detecting correlations between incidents
• Suggesting quick fixes and resolutions
• Recommending escalation when needed

Currently loaded with sample incidents from your knowledge base.
""")


def print_stats(kb):
    """Print system statistics"""
    incidents = kb.get_all_incidents()
    print(f"📊 System Status:")
    print(f"   • Total incidents in knowledge base: {len(incidents)}")

    systems = {}
    severities = {}
    for inc in incidents:
        systems[inc['system']] = systems.get(inc['system'], 0) + 1
        severities[inc['severity']] = severities.get(inc['severity'], 0) + 1

    print(f"   • Systems covered: {', '.join(systems.keys())}")
    print(f"   • Severity distribution: {severities}")
    print()


def get_incident_input():
    """Get incident details from user input"""
    print("🚨 Incident Report Form")
    print("-" * 30)

    title = input("Incident Title: ").strip()
    if not title:
        print("❌ Title is required.")
        return None

    print("Description (press Enter twice when done):")
    description_lines = []
    while True:
        line = input()
        if line == "" and description_lines and description_lines[-1] == "":
            break
        description_lines.append(line)

    description = "\n".join(description_lines).strip()
    if not description:
        print("❌ Description is required.")
        return None

    return {
        "title": title,
        "description": description
    }


def display_results(result):
    """Display analysis results in a formatted way"""
    print("\n" + "="*60)
    print("📋 ANALYSIS RESULTS")
    print("="*60)

    # Summary
    confidence_pct = result.confidence * 100
    confidence_icon = "🟢" if confidence_pct > 80 else "🟡" if confidence_pct > 60 else "🔴"

    print(f"🎯 Confidence Score: {confidence_icon} {confidence_pct:.1f}%")
    print(f"⚡ Escalation Needed: {'Yes' if result.result['needs_escalation'] else 'No'}")

    if result.result['needs_escalation']:
        print(f"   Reason: {result.result.get('escalation_reason', 'Unknown')}")

    # Classification
    cls = result.result['classification']
    print(f"\n🏷️  CLASSIFICATION:")
    print(f"   System: {cls['system']}")
    print(f"   Type: {cls['incident_type']}")
    print(f"   Severity: {cls['severity']}")
    print(f"   Components: {', '.join(cls['affected_components']) if cls['affected_components'] else 'None identified'}")

    # Similar incidents
    similar = result.result['similar_incidents']
    print(f"\n🔍 SIMILAR INCIDENTS ({len(similar)} found):")
    if similar:
        for i, inc in enumerate(similar[:5], 1):
            print(f"   {i}. {inc['id']} (similarity: {inc['similarity_score']:.1%})")
            print(f"      {inc['description'][:100]}{'...' if len(inc['description']) > 100 else ''}")
    else:
        print("   No similar incidents found in knowledge base.")

    # Correlations
    correlations = result.result['correlations']
    print(f"\n🔗 CORRELATED INCIDENTS ({len(correlations)} found):")
    if correlations:
        for corr in correlations:
            print(f"   • {corr}")
    else:
        print("   No correlated incidents detected.")

    # Quick fixes
    fixes = result.result['quick_fixes']
    print(f"\n🔧 RECOMMENDED QUICK FIXES ({len(fixes)} available):")
    if fixes:
        for i, fix in enumerate(fixes, 1):
            print(f"   {i}. {fix['description']}")
            print(f"      Estimated time: {fix['estimated_time']}")
            if 'source_incident' in fix:
                print(f"      Based on: {fix['source_incident']}")
    else:
        print("   No quick fixes available for this incident type.")

    # Recommendations
    recommendations = result.recommendations
    print(f"\n💡 AI RECOMMENDATIONS:")
    if recommendations:
        for rec in recommendations:
            print(f"   • {rec}")
    else:
        print("   No specific recommendations available.")

    print("\n" + "="*60)


async def main():
    """Main interactive loop"""
    print_banner()

    # Initialize components
    print("🔧 Initializing AI Ops Copilot...")
    kb = KnowledgeBase()
    l1_agent = L1TriageAgent(kb)
    print("✅ System ready!\n")

    print_stats(kb)

    while True:
        print("Choose an option:")
        print("1. Analyze new incident")
        print("2. View system statistics")
        print("3. Exit")

        choice = input("\nEnter choice (1-3): ").strip()

        if choice == "1":
            # Get incident input
            incident_data = get_incident_input()
            if not incident_data:
                continue

            print("\n⚙️  Analyzing incident...")

            # Generate incident ID
            import uuid
            incident_id = f"INC_CLI_{uuid.uuid4().hex[:8].upper()}"

            # Create agent input
            input_data = AgentInput(
                incident_id=incident_id,
                data=incident_data
            )

            # Process through L1 agent
            result = await l1_agent.process(input_data)

            # Display results
            display_results(result)

        elif choice == "2":
            print_stats(kb)

        elif choice == "3":
            print("👋 Thank you for using AI Ops Copilot!")
            break

        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

        print()  # Empty line for spacing


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Session ended by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()