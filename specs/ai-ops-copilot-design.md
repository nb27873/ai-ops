# AI Ops Copilot System Design Document (SDD)

## 1. Overview

The AI Ops Copilot system is designed to assist in incident management for IT operations, leveraging multiple AI agents with specialized responsibilities. The system automates incident triage, analysis, resolution, and escalation processes to reduce mean time to resolution (MTTR) and improve operational efficiency.

### 1.1 Purpose
- Automate incident classification and triage
- Provide intelligent suggestions for resolution
- Enable proactive pattern detection and prevention
- Facilitate knowledge sharing through historical incident analysis

### 1.2 Scope
The system covers incident management for multiple systems including GCP, Talend, Kafka, and batch processing pipelines. It handles various incident types such as ingestion failures, authentication issues, pipeline delays, and data quality problems.

## 2. System Architecture

### 2.1 High-Level Architecture
```
[Incident Input]
       |
       v
[L1 - Incident Triage Agent] --> [Knowledge Retrieval Agent]
       |                           ^
       v                           |
[L2 - Analysis Agent] <----------> [Pattern Mining Agent]
       |
       v
[Runbook/Resolution Agent] --> [Escalation Agent]
       |
       v
[Resolution Output / Escalation]
```

### 2.2 Agent Responsibilities

#### L1 - Incident Triage Agent (AO Team)
- **Primary Functions:**
  - Classifies incoming incidents by system, type, and severity
  - Identifies affected systems (GCP, Talend, Kafka, etc.)
  - Detects incident types (ingestion failure, auth issue, pipeline delay, etc.)
  - Finds similar past incidents using similarity matching
  - Suggests quick fixes based on historical data
  - Correlates multiple incidents to identify patterns
  - Groups related incidents
  - Identifies possible systemic or upstream issues
  - Escalates to L2 when issues exceed L1 capabilities

- **Input:** Raw incident description, logs, error messages
- **Output:** Classified incident with suggested quick fixes, correlation groups, escalation recommendation

#### L2 - Analysis Agent (AM Team)
- **Primary Functions:**
  - Determines probable root cause through hypothesis testing
  - Validates hypotheses using historical incident data
  - Produces structured Root Cause Analysis (RCA) reports
  - Suggests long-term preventive actions
  - Handles complex incident analysis requiring deep technical knowledge

- **Input:** Classified incident from L1, historical context
- **Output:** Detailed RCA report, preventive recommendations

#### Knowledge Retrieval (RAG) Agent
- **Primary Functions:**
  - Searches historical incident knowledge base using Retrieval-Augmented Generation
  - Provides relevant context and similar incidents to other agents
  - Maintains and updates the incident knowledge base
  - Enables semantic search across incident descriptions and resolutions

- **Input:** Query strings, incident details
- **Output:** Relevant historical incidents, context snippets, knowledge articles

#### Pattern Mining Agent
- **Primary Functions:**
  - Identifies recurring operational patterns in incident data
  - Updates taxonomy of issues and systems dynamically
  - Suggests new categories or groupings for incidents
  - Generates insights for proactive monitoring and alerting

- **Input:** Historical incident data, current incident patterns
- **Output:** Updated taxonomy, pattern reports, categorization suggestions

#### Runbook / Resolution Agent
- **Primary Functions:**
  - Converts RCA findings into actionable remediation steps
  - Generates standardized runbooks for common incident types
  - Suggests step-by-step resolution procedures
  - Validates resolution steps against historical success rates

- **Input:** RCA report from L2, incident details
- **Output:** Actionable runbook, resolution steps with confidence scores

#### Escalation Agent
- **Primary Functions:**
  - Evaluates confidence levels of AI-generated outputs
  - Determines whether incidents require human engineer intervention
  - Flags unknown or high-risk incidents for immediate escalation
  - Provides escalation rationale and priority recommendations

- **Input:** Outputs from all agents, confidence scores
- **Output:** Escalation decision, priority level, human assignment recommendations

## 3. Incident Response Workflow

### 3.1 Standard Incident Flow

1. **Incident Ingestion**
   - Incident received via ticketing system, monitoring alerts, or manual submission
   - Initial parsing of incident description, logs, and metadata

2. **L1 Classification (Incident Triage Agent)**
   - Classify system, type, and severity
   - Search for similar historical incidents
   - Apply quick fixes if confidence > 80%
   - Correlate with other active incidents
   - Escalate to L2 if:
     - No similar incidents found
     - Quick fixes unsuccessful
     - Incident involves multiple systems
     - High severity or business impact

3. **Knowledge Retrieval**
   - Parallel process: Retrieve relevant historical context
   - Provide context to L1 and L2 agents

4. **L2 Analysis (if escalated)**
   - Perform root cause analysis
   - Generate hypotheses and validate against historical data
   - Produce structured RCA report
   - Suggest preventive measures

5. **Resolution Planning**
   - Convert RCA to actionable steps
   - Generate runbook with step-by-step instructions
   - Validate steps against known successful resolutions

6. **Escalation Evaluation**
   - Assess confidence in AI recommendations
   - Determine if human intervention required
   - Flag high-risk or unknown scenarios

7. **Resolution or Escalation**
   - If confidence > 90%: Auto-resolve with monitoring
   - If confidence 70-90%: Suggest resolution with human approval
   - If confidence < 70%: Escalate to human engineers

### 3.2 Parallel Processing
- Pattern mining runs continuously in background
- Knowledge retrieval supports all agents simultaneously
- Escalation evaluation occurs at multiple decision points

## 4. Data Model

### 4.1 Incident Schema
```json
{
  "id": "INC000098188704",
  "title": "Multiple Dmaap jobs abort (Conn Issue)",
  "description": "SFTP connection failure to 10.59.2.4",
  "system": "Talend",
  "type": "ingestion_failure",
  "severity": "P2",
  "status": "resolved",
  "created_date": "2025-12-05",
  "resolved_date": "2026-02-03",
  "root_cause": "SFTP server connectivity issue",
  "resolution_steps": ["Restart SFTP service", "Verify network connectivity"],
  "similar_incidents": ["INC000099266256", "INC000099274091"],
  "tags": ["sftp", "connectivity", "dmaap"]
}
```

### 4.2 Knowledge Base Structure
- **Incidents:** Stored as markdown files with structured metadata
- **Taxonomy:** Hierarchical classification of systems, types, and severities
- **Patterns:** Identified recurring issues with frequency and impact metrics
- **Runbooks:** Standardized resolution procedures by incident type

## 5. Technical Implementation

### 5.1 Agent Framework
- **Language:** Python with LangChain/LlamaIndex for agent orchestration
- **LLM:** GPT-4 or similar for reasoning and generation tasks
- **Vector Database:** Pinecone/Weaviate for semantic search
- **Storage:** File system for incident markdowns, database for metadata

### 5.2 Key Components
- **Incident Parser:** Extracts structured data from raw incident descriptions
- **Similarity Engine:** Cosine similarity on embeddings for incident matching
- **RCA Generator:** Structured analysis with hypothesis testing
- **Confidence Scorer:** Bayesian approach for output confidence assessment

### 5.3 Integration Points
- **Ticketing System:** ServiceNow/Jira integration for incident ingestion
- **Monitoring:** Prometheus/Grafana for alert correlation
- **Knowledge Base:** Git-based storage with automated updates

## 6. Success Metrics

### 6.1 Operational Metrics
- Mean Time to Triage (MTTT)
- Mean Time to Resolution (MTTR)
- Escalation Rate
- Auto-resolution Rate

### 6.2 Quality Metrics
- Accuracy of classification
- Effectiveness of suggested resolutions
- User satisfaction scores
- Reduction in recurring incidents

## 7. Risk Assessment

### 7.1 Technical Risks
- LLM hallucinations in critical decisions
- Incomplete or biased historical data
- Integration failures with existing systems

### 7.2 Mitigation Strategies
- Human-in-the-loop validation for high-risk incidents
- Continuous model fine-tuning with feedback
- Fallback procedures for agent failures
- Confidence thresholds for automated actions

## 8. Future Enhancements

### 8.1 Phase 2 Features
- Predictive incident detection
- Automated remediation execution
- Multi-language support
- Advanced correlation with metrics data

### 8.2 Research Areas
- Causal inference for root cause analysis
- Reinforcement learning for resolution optimization
- Multi-modal incident analysis (logs + metrics + traces)