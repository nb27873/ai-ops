"""
FastAPI Backend for AI Ops Copilot Web Interface
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import asyncio
from pathlib import Path

from agents.l1_triage_agent import L1TriageAgent
from agents.quality_agent import QualityAgent
from agents.base_agent import AgentInput
from knowledge.knowledge_base import KnowledgeBase


app = FastAPI(title="AI Ops Copilot", description="Incident Management AI System")

# Initialize components
kb = KnowledgeBase()
l1_agent = L1TriageAgent(kb)
quality_agent = QualityAgent()


class IncidentRequest(BaseModel):
    title: str
    description: str
    system: Optional[str] = None
    severity: Optional[str] = None
    validate_template: Optional[bool] = False
    raw_content: Optional[str] = None


class IncidentResponse(BaseModel):
    incident_id: str
    classification: dict
    similar_incidents: list
    correlations: list
    quick_fixes: list
    confidence: float
    needs_escalation: bool
    escalation_reason: str
    recommendations: list
    quality_validation: Optional[dict] = None


@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    """Serve the main frontend page"""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Ops Copilot</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { max-width: 800px; margin: 0 auto; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; }
                input, textarea { width: 100%; padding: 8px; }
                button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
                .results { margin-top: 20px; padding: 15px; border: 1px solid #ddd; }
                .confidence { font-weight: bold; }
                .high-confidence { color: green; }
                .medium-confidence { color: orange; }
                .low-confidence { color: red; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 AI Ops Copilot</h1>
                <p>Enter incident details for intelligent analysis and correlation detection.</p>

                <form id="incidentForm">
                    <div class="form-group">
                        <label for="title">Incident Title:</label>
                        <input type="text" id="title" required placeholder="e.g., SFTP Connection Failure">
                    </div>

                    <div class="form-group">
                        <label for="description">Description:</label>
                        <textarea id="description" rows="6" required placeholder="Describe the incident in detail..."></textarea>
                    </div>

                    <div class="form-group">
                        <label for="raw_content">Optional full incident markdown</label>
                        <textarea id="raw_content" rows="5" placeholder="Paste full incident markdown for template validation..."></textarea>
                    </div>

                    <div class="form-group">
                        <label><input type="checkbox" id="validate_template"> Validate against incident template</label>
                    </div>

                    <button type="submit">Analyze Incident</button>
                </form>

                <div id="results" class="results" style="display: none;">
                    <h2>Analysis Results</h2>
                    <div id="resultsContent"></div>
                </div>
            </div>

            <script>
                document.getElementById('incidentForm').addEventListener('submit', async (e) => {
                    e.preventDefault();

                    const title = document.getElementById('title').value;
                    const description = document.getElementById('description').value;
                const rawContent = document.getElementById('raw_content').value;
                const validateTemplate = document.getElementById('validate_template').checked;

                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title,
                        description,
                        raw_content: rawContent,
                        validate_template: validateTemplate
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                displayResults(result);
            });

                function displayResults(result) {
                    const resultsDiv = document.getElementById('results');
                    const contentDiv = document.getElementById('resultsContent');

                    let confidenceClass = 'low-confidence';
                    if (result.confidence > 0.8) confidenceClass = 'high-confidence';
                    else if (result.confidence > 0.6) confidenceClass = 'medium-confidence';

                    let html = `
                        <p><strong>Confidence:</strong> <span class="confidence ${confidenceClass}">${(result.confidence * 100).toFixed(1)}%</span></p>
                        <p><strong>Needs Escalation:</strong> ${result.needs_escalation ? 'Yes' : 'No'}</p>

                        <h3>🏷️ Classification</h3>
                        <ul>
                            <li><strong>System:</strong> ${result.classification.system}</li>
                            <li><strong>Type:</strong> ${result.classification.incident_type}</li>
                            <li><strong>Severity:</strong> ${result.classification.severity}</li>
                            <li><strong>Components:</strong> ${result.classification.affected_components.join(', ')}</li>
                        </ul>

                        <h3>🔍 Similar Incidents</h3>
                        ${result.similar_incidents.length > 0 ?
                            '<ul>' + result.similar_incidents.map(inc =>
                                `<li>${inc.id} (similarity: ${(inc.similarity_score * 100).toFixed(1)}%)</li>`
                            ).join('') + '</ul>' :
                            '<p>No similar incidents found</p>'
                        }

                        <h3>🔗 Correlated Incidents</h3>
                        ${result.correlations.length > 0 ?
                            `<p>${result.correlations.join(', ')}</p>` :
                            '<p>No correlated incidents found</p>'
                        }

                        <h3>🔧 Quick Fixes</h3>
                        ${result.quick_fixes.length > 0 ?
                            '<ol>' + result.quick_fixes.map(fix =>
                                `<li><strong>${fix.description}</strong><br>Estimated time: ${fix.estimated_time}</li>`
                            ).join('') + '</ol>' :
                            '<p>No quick fixes available</p>'
                        }

                        ${result.needs_escalation ?
                            `<h3>⚠️ Escalation Reason</h3><p>${result.escalation_reason}</p>` :
                            ''
                        }
                        ${result.quality_validation ?
                            `<h3>✅ Template Compliance</h3>
                             <p><strong>Score:</strong> ${result.quality_validation.required_field_score}%</p>
                             <p><strong>Summary:</strong> ${result.quality_validation.summary}</p>
                             ${result.quality_validation.missing_required_fields.length > 0 ? `<p><strong>Missing fields:</strong> ${result.quality_validation.missing_required_fields.join(', ')}</p>` : ''}` : ''
                        }

                        <h3>💡 Recommendations</h3>
                        <ul>
                            ${result.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    `;

                    contentDiv.innerHTML = html;
                    resultsDiv.style.display = 'block';
                }
            </script>
        </body>
        </html>
        """


@app.post("/analyze", response_model=IncidentResponse)
async def analyze_incident(request: IncidentRequest):
    """Analyze an incident using the L1 triage agent"""
    try:
        # Generate incident ID
        import uuid
        incident_id = f"INC_WEB_{uuid.uuid4().hex[:8].upper()}"

        # Create agent input
        input_data = AgentInput(
            incident_id=incident_id,
            data={
                "title": request.title,
                "description": request.description,
                "system": request.system,
                "severity": request.severity
            }
        )

        # Process through L1 agent
        result = await l1_agent.process(input_data)

        # Convert result to response format
        quality_validation = None
        if request.validate_template:
            quality_input = AgentInput(
                incident_id=incident_id,
                data={
                    "title": request.title,
                    "description": request.description,
                    "raw_content": request.raw_content or request.description
                }
            )
            quality_result = await quality_agent.process(quality_input)
            quality_validation = quality_result.result.get('quality_validation')

        response = IncidentResponse(
            incident_id=result.incident_id,
            classification=result.result['classification'],
            similar_incidents=result.result['similar_incidents'],
            correlations=result.result['correlations'],
            quick_fixes=result.result['quick_fixes'],
            confidence=result.confidence,
            needs_escalation=result.result['needs_escalation'],
            escalation_reason=result.result.get('escalation_reason', ''),
            recommendations=result.recommendations,
            quality_validation=quality_validation
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/incidents")
async def get_incidents():
    """Get list of all incidents in the knowledge base"""
    try:
        incidents = kb.get_all_incidents()
        return {"incidents": incidents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve incidents: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "incidents_loaded": len(kb.get_all_incidents())}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)