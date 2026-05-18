"""
Knowledge Base for Incident Management
Provides RAG capabilities for historical incident retrieval
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

"""
Knowledge Base for Incident Management
Provides RAG capabilities for historical incident retrieval
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import re
from difflib import SequenceMatcher

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import chromadb, fallback to simple implementation if not available
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    logger.warning("ChromaDB not available, using simple in-memory implementation")
    CHROMADB_AVAILABLE = False


class KnowledgeBase:
    """Knowledge base for storing and retrieving incident information"""

    def __init__(self, incidents_path: str = "knowledge/incidents",
                 chroma_path: str = "data/chroma"):
        self.incidents_path = Path(incidents_path)
        self.incidents = []  # List of incident dicts

        if CHROMADB_AVAILABLE:
            self.chroma_path = Path(chroma_path)
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.chroma_path),
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.chroma_client.get_or_create_collection("incidents")
            self.use_chromadb = True
        else:
            self.use_chromadb = False
            logger.info("Using simple in-memory knowledge base")

        self._load_incidents()

    def _load_incidents(self):
        """Load incident data from markdown files"""
        if not self.incidents_path.exists():
            logger.warning(f"Incidents path {self.incidents_path} does not exist")
            return

        for md_file in self.incidents_path.glob("*.md"):
            if md_file.name.startswith('_'):
                continue  # Skip index files

            incident_id = md_file.stem
            if self.use_chromadb and self._is_incident_loaded(incident_id):
                continue

            try:
                content = self._parse_incident_file(md_file)

                if self.use_chromadb:
                    self._add_to_vector_store(incident_id, content)
                else:
                    # Store in memory
                    content['id'] = incident_id
                    self.incidents.append(content)

                logger.info(f"Loaded incident {incident_id}")
            except Exception as e:
                logger.error(f"Failed to load incident {incident_id}: {e}")

    def _parse_incident_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse incident markdown file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simple parsing - can be enhanced
        lines = content.split('\n')
        title = lines[0].replace('#', '').strip() if lines else "Unknown"

        # Extract description (simplified)
        description = ""
        in_description = False
        for line in lines:
            if line.startswith('Description:'):
                in_description = True
                continue
            elif in_description and line.startswith('Initial Diagnosis:'):
                break
            elif in_description:
                description += line + " "

        # Extract other fields
        system = "Unknown"
        incident_type = "other"
        severity = "medium"

        # Simple keyword extraction
        text = content.lower()
        if "gcp" in text:
            system = "GCP"
        elif "talend" in text:
            system = "Talend"
        elif "kafka" in text:
            system = "Kafka"

        if "p1" in text or "critical" in text:
            severity = "critical"
        elif "p2" in text or "high" in text:
            severity = "high"

        return {
            'title': title,
            'description': description.strip(),
            'system': system,
            'type': incident_type,
            'severity': severity,
            'full_content': content
        }

    def _add_to_vector_store(self, incident_id: str, content: Dict[str, Any]):
        """Add incident to vector store"""
        # Create searchable text
        searchable_text = f"{content['title']} {content['description']}"

        # Simple metadata
        metadata = {
            'system': content['system'],
            'type': content['type'],
            'severity': content['severity'],
            'incident_id': incident_id
        }

        self.collection.add(
            documents=[searchable_text],
            metadatas=[metadata],
            ids=[incident_id]
        )

    def _is_incident_loaded(self, incident_id: str) -> bool:
        """Check if incident is already in vector store"""
        try:
            result = self.collection.get(ids=[incident_id])
            return len(result['ids']) > 0
        except:
            return False

    async def find_similar_incidents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar incidents using semantic search"""
        if self.use_chromadb:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit,
                    include=['metadatas', 'documents', 'distances']
                )

                similar_incidents = []
                for i, incident_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]

                    similar_incidents.append({
                        'id': incident_id,
                        'system': metadata.get('system', 'Unknown'),
                        'type': metadata.get('type', 'other'),
                        'severity': metadata.get('severity', 'medium'),
                        'similarity_score': 1.0 - distance,  # Convert distance to similarity
                        'description': results['documents'][0][i][:200] + "..."  # Truncate
                    })

                return similar_incidents
            except Exception as e:
                logger.error(f"Error finding similar incidents: {e}")
                return []
        else:
            # Simple text similarity using difflib
            query_lower = query.lower()
            similarities = []

            for incident in self.incidents:
                text = f"{incident['title']} {incident['description']}".lower()
                similarity = SequenceMatcher(None, query_lower, text).ratio()
                similarities.append((incident, similarity))

            # Sort by similarity and take top results
            similarities.sort(key=lambda x: x[1], reverse=True)
            similar_incidents = []

            for incident, similarity in similarities[:limit]:
                similar_incidents.append({
                    'id': incident['id'],
                    'system': incident.get('system', 'Unknown'),
                    'type': incident.get('type', 'other'),
                    'severity': incident.get('severity', 'medium'),
                    'similarity_score': similarity,
                    'description': incident['description'][:200] + "..." if len(incident['description']) > 200 else incident['description']
                })

            return similar_incidents

    async def find_correlated_incidents(self, incident_id: str, system: str,
                                      incident_type: str) -> List[str]:
        """Find correlated incidents based on system and type"""
        if self.use_chromadb:
            try:
                # Query for incidents with same system and type
                results = self.collection.query(
                    query_texts=[f"{system} {incident_type}"],
                    n_results=10,
                    include=['metadatas']
                )

                correlated = []
                for metadata in results['metadatas'][0]:
                    corr_id = metadata.get('incident_id')
                    if corr_id and corr_id != incident_id:
                        correlated.append(corr_id)

                return correlated[:5]  # Limit to 5
            except Exception as e:
                logger.error(f"Error finding correlated incidents: {e}")
                return []
        else:
            # Simple correlation based on system and type
            correlated = []
            for incident in self.incidents:
                if (incident['id'] != incident_id and
                    incident.get('system') == system and
                    incident.get('type') == incident_type):
                    correlated.append(incident['id'])

            return correlated[:5]

    async def get_incident_details(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific incident"""
        if self.use_chromadb:
            try:
                result = self.collection.get(ids=[incident_id])
                if result['ids']:
                    metadata = result['metadatas'][0]
                    return {
                        'id': incident_id,
                        'system': metadata.get('system'),
                        'type': metadata.get('type'),
                        'severity': metadata.get('severity')
                    }
            except Exception as e:
                logger.error(f"Error getting incident details: {e}")
            return None
        else:
            for incident in self.incidents:
                if incident['id'] == incident_id:
                    return {
                        'id': incident_id,
                        'system': incident.get('system'),
                        'type': incident.get('type'),
                        'severity': incident.get('severity')
                    }
            return None

    def get_all_incidents(self) -> List[Dict[str, Any]]:
        """Get all incidents for web display"""
        if self.use_chromadb:
            try:
                results = self.collection.get(include=['metadatas'])
                incidents = []
                for i, incident_id in enumerate(results['ids']):
                    metadata = results['metadatas'][i]
                    incidents.append({
                        'id': incident_id,
                        'system': metadata.get('system', 'Unknown'),
                        'type': metadata.get('type', 'other'),
                        'severity': metadata.get('severity', 'medium')
                    })
                return incidents
            except Exception as e:
                logger.error(f"Error getting all incidents: {e}")
                return []
        else:
            return [{
                'id': inc['id'],
                'system': inc.get('system', 'Unknown'),
                'type': inc.get('type', 'other'),
                'severity': inc.get('severity', 'medium')
            } for inc in self.incidents]

    async def update_taxonomy(self, new_patterns: Dict[str, Any]):
        """Update incident taxonomy with new patterns"""
        # This would update the taxonomy.md file
        # Implementation depends on taxonomy structure
        pass