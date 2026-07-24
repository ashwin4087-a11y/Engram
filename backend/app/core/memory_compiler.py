import os
import anthropic
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.database import Entity, Fact, Episode

# Structured output definition for Anthropic Tools
class ExtractedEntity(BaseModel):
    name: str
    entity_type: str

class ExtractedFact(BaseModel):
    entity_name: str
    statement: str

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def compile_memory(text: str, session_id: str, db: Session):
    """
    Takes raw user text, runs it through Claude to extract entities and facts,
    and saves them to the PostgreSQL database.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set. Returning mock data.")
        return mock_extraction(text, session_id, db)

    system_prompt = "You are a memory extraction pipeline. Extract key entities (people, places, concepts) and atomic facts from the user's input. Only extract information that is explicitly stated."
    
    tools = [
        {
            "name": "save_memory",
            "description": "Saves extracted entities and facts into the world model.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "entity_type": {"type": "string", "enum": ["person", "object", "concept", "location", "task"]}
                            },
                            "required": ["name", "entity_type"]
                        }
                    },
                    "facts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity_name": {"type": "string"},
                                "statement": {"type": "string"}
                            },
                            "required": ["entity_name", "statement"]
                        }
                    },
                    "episode_summary": {
                        "type": "string",
                        "description": "A concise, one-sentence summary of the user's input representing a single raw episode of memory."
                    }
                },
                "required": ["entities", "facts", "episode_summary"]
            }
        }
    ]

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            system=system_prompt,
            tools=tools,
            tool_choice={"type": "tool", "name": "save_memory"},
            messages=[{"role": "user", "content": text}]
        )

        tool_use = None
        for content in response.content:
            if content.type == "tool_use" and content.name == "save_memory":
                tool_use = content
                break
        
        if tool_use:
            data = tool_use.input
            # Save to DB
            saved_entities = []
            saved_facts = []
            
            for ent in data.get('entities', []):
                db_ent = Entity(
                    session_id=session_id,
                    name=ent['name'],
                    entity_type=ent['entity_type']
                )
                db.add(db_ent)
                db.commit()
                db.refresh(db_ent)
                saved_entities.append(ent)
            
            for fact in data.get('facts', []):
                # Simple lookup to attach fact to entity (MVP logic)
                target_ent = db.query(Entity).filter(Entity.session_id == session_id, Entity.name == fact['entity_name']).first()
                ent_id = target_ent.id if target_ent else None
                
                db_fact = Fact(
                    session_id=session_id,
                    entity_id=ent_id,
                    statement=fact['statement'],
                    # We skip embeddings in this simple MVP step
                )
                db.add(db_fact)
                db.commit()
                saved_facts.append(fact)
                
            episode_summary = data.get('episode_summary')
            if episode_summary:
                db_episode = Episode(
                    session_id=session_id,
                    summary=episode_summary,
                    level=0,
                    decayed=False
                )
                db.add(db_episode)
                db.commit()
                
            return {"entities": saved_entities, "facts": saved_facts, "episode": episode_summary}
    except Exception as e:
        print(f"Error during memory extraction: {e}")
    
    return {"entities": [], "facts": []}

def mock_extraction(text: str, session_id: str, db: Session):
    # Mock fallback if no API key
    if "Berlin" in text:
        ent = Entity(session_id=session_id, name="User", entity_type="person")
        db.add(ent)
        db.commit()
        db.refresh(ent)
        fact = Fact(session_id=session_id, entity_id=ent.id, statement="User moved to Berlin")
        db.add(fact)
        db.commit()
        return {"entities": [{"name": "User", "type": "person"}], "facts": [{"statement": "User moved to Berlin"}]}
    return {"entities": [], "facts": []}
