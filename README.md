# AI Ops Copilot System

An intelligent incident management system using multiple AI agents to automate incident triage, analysis, and resolution.

## Overview

The AI Ops Copilot system leverages specialized AI agents to handle different aspects of incident management:

- **L1 Incident Triage Agent**: Classifies incidents, finds similar cases, suggests quick fixes
- **Quality Agent**: Validates incident markdown against the expected template and scores template compliance
- **L2 Analysis Agent**: Performs root cause analysis and suggests preventive measures
- **Knowledge Retrieval Agent**: Provides RAG-based access to historical incident data
- **Pattern Mining Agent**: Identifies recurring patterns and updates taxonomy
- **Runbook/Resolution Agent**: Converts analysis into actionable remediation steps
- **Escalation Agent**: Determines when human intervention is required

## Architecture

```
[Incident Input]
       |
       v
[L1 - Incident Triage] --> [Knowledge Retrieval]
       |                      ^
       v                      |
[L2 - Root Cause Analysis] --> [Pattern Mining]
       |
       v
[Resolution Planning] --> [Escalation Check]
       |
       v
[Auto-Resolution / Human Escalation]
```

## Quick Start

### Interactive Demo (Recommended)
```bash
python interactive_demo.py
```

This launches an interactive command-line interface where you can:
- Input incident details (title and description)
- See real-time AI analysis and classification
- View similar historical incidents
- Get correlation insights
- Receive quick fix recommendations
- Get escalation advice

### Automated Demo
```bash
python run_copilot.py
```

Runs a demonstration with a pre-configured sample incident.

### Web Interface (Requires Additional Setup)
For the full web interface, you'll need to install web dependencies:
```bash
pip install flask fastapi uvicorn
```

Then run:
```bash
# Flask version
python flask_app.py

# Or FastAPI version
python web_app.py
```

Open http://localhost:5000 (Flask) or http://localhost:8000 (FastAPI) in your browser.

## Project Structure

```
ai-ops-copilot/
├── agents/                 # AI agent implementations
│   ├── base_agent.py      # Abstract base agent class
│   └── l1_triage_agent.py # L1 incident triage agent
├── knowledge/             # Knowledge base and RAG
│   ├── knowledge_base.py  # Vector store and retrieval
│   ├── incidents/         # Historical incident data
│   └── taxonomy.md        # Incident classification taxonomy
├── specs/                 # System specifications
│   ├── incident-understanding.md
│   └── ai-ops-copilot-design.md
├── requirements.txt       # Python dependencies
├── run_copilot.py         # Demo runner
└── README.md
```

## Incident Response Workflow

1. **Incident Ingestion**: Raw incident data is received
2. **L1 Classification**: System, type, severity classification + similar incident search
3. **Quick Resolution**: Apply known fixes if confidence > 80%
4. **L2 Analysis**: Root cause analysis for complex issues
5. **Resolution Planning**: Generate actionable runbooks
6. **Escalation Check**: Determine if human intervention needed
7. **Resolution**: Auto-resolve or escalate to engineers

## Key Features

- **Intelligent Classification**: Automatic system and incident type detection
- **Historical Matching**: Semantic search for similar past incidents
- **Quick Fixes**: Rule-based and ML-driven resolution suggestions
- **Root Cause Analysis**: Structured RCA with hypothesis validation
- **Knowledge Base**: RAG-powered retrieval of incident history
- **Pattern Recognition**: Automated detection of recurring issues
- **Confidence Scoring**: Bayesian confidence assessment for recommendations
- **Human-in-the-Loop**: Escalation logic for high-risk scenarios

## Configuration

The system uses the following key parameters:

- **Confidence Thresholds**:
  - Auto-resolution: > 90%
  - Human approval: 70-90%
  - Escalation: < 70%

- **Agent Models**: GPT-4 for reasoning tasks
- **Vector Store**: ChromaDB for semantic search
- **Similarity Threshold**: 0.8 for incident matching

## Development

### Adding New Agents

1. Extend `BaseAgent` class
2. Implement `process()` method
3. Add agent to the workflow orchestration

### Training Data

- Incident data stored in `knowledge/incidents/` as markdown files
- Taxonomy defined in `knowledge/taxonomy.md`
- Patterns updated automatically by Pattern Mining Agent

## Metrics

- **MTTT**: Mean Time to Triage
- **MTTR**: Mean Time to Resolution
- **Auto-resolution Rate**: Percentage of incidents resolved automatically
- **Escalation Accuracy**: Correctness of escalation decisions

## Future Enhancements

- Predictive incident detection
- Automated remediation execution
- Multi-modal analysis (logs + metrics + traces)
- Advanced causal inference for RCA
- Reinforcement learning optimization