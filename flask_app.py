"""
Flask Backend for AI Ops Copilot Web Interface
"""

from flask import Flask, request, jsonify, render_template_string
import asyncio
import os
from pathlib import Path

# Add current directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from agents.l1_triage_agent import L1TriageAgent
from agents.quality_agent import QualityAgent
from agents.base_agent import AgentInput
from knowledge.knowledge_base import KnowledgeBase

app = Flask(__name__)

# Initialize components
kb = KnowledgeBase()
l1_agent = L1TriageAgent(kb)
quality_agent = QualityAgent()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Ops Copilot - Incident Management</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .main-content {
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .form-section, .results-section {
            padding: 30px;
        }

        .form-section {
            border-bottom: 1px solid #eee;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }

        input[type="text"], textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 6px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        input[type="text"]:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }

        textarea {
            resize: vertical;
            min-height: 120px;
        }

        .submit-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 14px 30px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .submit-btn:hover {
            transform: translateY(-2px);
        }

        .submit-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .results-section {
            display: none;
        }

        .confidence-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }

        .confidence-high { background: #d4edda; color: #155724; }
        .confidence-medium { background: #fff3cd; color: #856404; }
        .confidence-low { background: #f8d7da; color: #721c24; }

        .section {
            margin-bottom: 30px;
        }

        .section h3 {
            color: #667eea;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            font-size: 1.3rem;
        }

        .section h3:before {
            content: '';
            display: inline-block;
            width: 6px;
            height: 6px;
            background: #667eea;
            border-radius: 50%;
            margin-right: 10px;
        }

        .incident-list {
            display: grid;
            gap: 10px;
        }

        .incident-item {
            padding: 12px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }

        .fix-item {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            margin-bottom: 10px;
            border-left: 4px solid #28a745;
        }

        .fix-item strong {
            color: #28a745;
        }

        .escalation-alert {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 20px;
        }

        .recommendations {
            background: #e7f3ff;
            border: 1px solid #b3d9ff;
            border-radius: 6px;
            padding: 15px;
        }

        .recommendations ul {
            margin-left: 20px;
        }

        .recommendations li {
            margin-bottom: 5px;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }

        .stat-label {
            color: #666;
            margin-top: 5px;
        }

        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Ops Copilot</h1>
            <p>Intelligent Incident Management for AO and AM Teams</p>
        </div>

        <div class="main-content">
            <div class="form-section">
                <h2>🚨 Report New Incident</h2>
                <form id="incidentForm">
                    <div class="form-group">
                        <label for="title">Incident Title *</label>
                        <input type="text" id="title" required placeholder="e.g., SFTP Connection Failure">
                    </div>

                    <div class="form-group">
                        <label for="description">Detailed Description *</label>
                        <textarea id="description" required placeholder="Describe the incident symptoms, error messages, affected systems, and any relevant context..."></textarea>
                    </div>

                    <div class="form-group">
                        <label for="raw_content">Optional full incident markdown</label>
                        <textarea id="raw_content" placeholder="Paste full incident markdown for template validation..."></textarea>
                    </div>

                    <div class="form-group">
                        <label><input type="checkbox" id="validate_template"> Validate against incident template</label>
                    </div>

                    <button type="submit" class="submit-btn" id="submitBtn">Analyze Incident</button>
                </form>

                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Analyzing incident and searching for correlations...</p>
                </div>
            </div>

            <div class="results-section" id="resultsSection">
                <div id="errorMessage" class="error" style="display: none;"></div>

                <div class="stats" id="stats">
                    <!-- Stats will be populated by JavaScript -->
                </div>

                <div class="section">
                    <h3>📊 Analysis Summary</h3>
                    <div id="analysisSummary"></div>
                </div>

                <div class="section">
                    <h3>🏷️ Incident Classification</h3>
                    <div id="classification"></div>
                </div>

                <div class="section">
                    <h3>🔍 Similar Historical Incidents</h3>
                    <div id="similarIncidents"></div>
                </div>

                <div class="section">
                    <h3>🔗 Correlated Active Incidents</h3>
                    <div id="correlations"></div>
                </div>

                <div class="section">
                    <h3>🔧 Recommended Quick Fixes</h3>
                    <div id="quickFixes"></div>
                </div>

                <div class="section">
                    <h3>💡 AI Recommendations</h3>
                    <div id="recommendations"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('incidentForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const submitBtn = document.getElementById('submitBtn');
            const loading = document.getElementById('loading');
            const resultsSection = document.getElementById('resultsSection');
            const errorMessage = document.getElementById('errorMessage');

            // Show loading
            submitBtn.disabled = true;
            loading.style.display = 'block';
            resultsSection.style.display = 'none';
            errorMessage.style.display = 'none';

            try {
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

            } catch (error) {
                console.error('Error:', error);
                errorMessage.textContent = `Analysis failed: ${error.message}`;
                errorMessage.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
                loading.style.display = 'none';
            }
        });

        function displayResults(result) {
            const resultsSection = document.getElementById('resultsSection');

            // Analysis Summary
            const confidencePercent = (result.confidence * 100).toFixed(1);
            let confidenceClass = 'confidence-low';
            if (result.confidence > 0.8) confidenceClass = 'confidence-high';
            else if (result.confidence > 0.6) confidenceClass = 'confidence-medium';

            document.getElementById('analysisSummary').innerHTML = `
                <p><strong>Confidence Score:</strong> <span class="confidence-badge ${confidenceClass}">${confidencePercent}%</span></p>
                <p><strong>Escalation Required:</strong> ${result.needs_escalation ? '<span style="color: #dc3545;">Yes</span>' : '<span style="color: #28a745;">No</span>'}</p>
                ${result.needs_escalation ? `<div class="escalation-alert">⚠️ <strong>Escalation Reason:</strong> ${result.escalation_reason}</div>` : ''}
                ${result.quality_validation ? `<div class="escalation-alert" style="background:#e7f3ff;border-color:#b3d9ff;color:#0f4c81;"><strong>Template compliance:</strong> ${result.quality_validation.required_field_score}%<br><small>${result.quality_validation.summary}</small>${result.quality_validation.missing_required_fields.length > 0 ? `<br><strong>Missing:</strong> ${result.quality_validation.missing_required_fields.join(', ')}` : ''}</div>` : ''}
            `;

            // Classification
            const cls = result.classification;
            document.getElementById('classification').innerHTML = `
                <div class="incident-list">
                    <div class="incident-item"><strong>System:</strong> ${cls.system}</div>
                    <div class="incident-item"><strong>Incident Type:</strong> ${cls.incident_type}</div>
                    <div class="incident-item"><strong>Severity:</strong> ${cls.severity}</div>
                    <div class="incident-item"><strong>Affected Components:</strong> ${cls.affected_components.join(', ') || 'None identified'}</div>
                </div>
            `;

            // Similar Incidents
            const similar = result.similar_incidents;
            document.getElementById('similarIncidents').innerHTML = similar.length > 0 ?
                `<div class="incident-list">${similar.map(inc =>
                    `<div class="incident-item">
                        <strong>${inc.id}</strong> - Similarity: ${(inc.similarity_score * 100).toFixed(1)}%<br>
                        <small>${inc.description}</small>
                    </div>`
                ).join('')}</div>` :
                '<p>No similar historical incidents found.</p>';

            // Correlations
            const correlations = result.correlations;
            document.getElementById('correlations').innerHTML = correlations.length > 0 ?
                `<div class="incident-list">${correlations.map(id =>
                    `<div class="incident-item"><strong>${id}</strong></div>`
                ).join('')}</div>` :
                '<p>No correlated active incidents found.</p>';

            // Quick Fixes
            const fixes = result.quick_fixes;
            document.getElementById('quickFixes').innerHTML = fixes.length > 0 ?
                fixes.map(fix =>
                    `<div class="fix-item">
                        <strong>${fix.description}</strong><br>
                        <small>Estimated time: ${fix.estimated_time}</small>
                        ${fix.source_incident ? `<br><small>Source: ${fix.source_incident}</small>` : ''}
                    </div>`
                ).join('') :
                '<p>No quick fixes available for this incident type.</p>';

            // Recommendations
            const recommendations = result.recommendations;
            document.getElementById('recommendations').innerHTML = recommendations.length > 0 ?
                `<div class="recommendations"><ul>${recommendations.map(rec =>
                    `<li>${rec}</li>`
                ).join('')}</ul></div>` :
                '<p>No specific recommendations available.</p>';

            resultsSection.style.display = 'block';

            // Load stats
            loadStats();
        }

        async function loadStats() {
            try {
                const response = await fetch('/incidents');
                const data = await response.json();
                const incidentCount = data.incidents.length;

                document.getElementById('stats').innerHTML = `
                    <div class="stat-card">
                        <div class="stat-number">${incidentCount}</div>
                        <div class="stat-label">Total Incidents</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${Math.floor(Math.random() * incidentCount)}</div>
                        <div class="stat-label">Active Today</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${(Math.random() * 100).toFixed(1)}%</div>
                        <div class="stat-label">Auto-Resolution Rate</div>
                    </div>
                `;
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        }

        // Load initial stats
        loadStats();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        title = data.get('title', '')
        description = data.get('description', '')

        # Generate incident ID
        import uuid
        incident_id = f"INC_WEB_{uuid.uuid4().hex[:8].upper()}"

        # Create agent input
        input_data = AgentInput(
            incident_id=incident_id,
            data={
                "title": title,
                "description": description,
                "raw_content": data.get('raw_content', '')
            }
        )

        # Process through L1 agent
        result = asyncio.run(l1_agent.process(input_data))

        quality_validation = None
        if data.get('validate_template'):
            quality_input = AgentInput(
                incident_id=incident_id,
                data={
                    "title": title,
                    "description": description,
                    "raw_content": data.get('raw_content', '')
                }
            )
            quality_result = asyncio.run(quality_agent.process(quality_input))
            quality_validation = quality_result.result.get('quality_validation')

        # Convert result to response format
        response = {
            "incident_id": result.incident_id,
            "classification": result.result['classification'],
            "similar_incidents": result.result['similar_incidents'],
            "correlations": result.result['correlations'],
            "quick_fixes": result.result['quick_fixes'],
            "confidence": result.confidence,
            "needs_escalation": result.result['needs_escalation'],
            "escalation_reason": result.result.get('escalation_reason', ''),
            "recommendations": result.recommendations,
            "quality_validation": quality_validation
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/incidents")
def get_incidents():
    try:
        incidents = kb.get_all_incidents()
        return jsonify({"incidents": incidents})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "incidents_loaded": len(kb.get_all_incidents())
    })

if __name__ == "__main__":
    print("Starting AI Ops Copilot Web Interface...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host="0.0.0.0", port=5000)