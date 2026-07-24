import os
import anthropic
from sqlalchemy.orm import Session
from ..models.database import Episode
from typing import List

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def run_sleep_cycle(session_id: str, db: Session):
    """
    Consolidates raw episodic memories (level=0) into a single summarized parent episode (level=1).
    Decays the original raw episodes.
    """
    raw_episodes = db.query(Episode).filter(
        Episode.session_id == session_id,
        Episode.level == 0,
        Episode.decayed == False
    ).all()
    
    if len(raw_episodes) < 2:
        return {"status": "skipped", "message": "Not enough episodes to consolidate."}

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set. Returning mock consolidated episode.")
        return mock_consolidation(raw_episodes, session_id, db)

    # Prepare episodes text for Claude
    episodes_text = "\n".join([f"- {ep.summary}" for ep in raw_episodes])
    
    system_prompt = "You are a memory consolidation engine. Your task is to compress a list of raw episodic memories into a single, cohesive, and concise summary that captures the most important information."
    
    tools = [
        {
            "name": "save_consolidated_memory",
            "description": "Saves the consolidated summary.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "The final compressed summary of all the episodes."
                    }
                },
                "required": ["summary"]
            }
        }
    ]

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            system=system_prompt,
            tools=tools,
            tool_choice={"type": "tool", "name": "save_consolidated_memory"},
            messages=[{"role": "user", "content": f"Consolidate the following episodes:\n{episodes_text}"}]
        )

        tool_use = None
        for content in response.content:
            if content.type == "tool_use" and content.name == "save_consolidated_memory":
                tool_use = content
                break
        
        if tool_use:
            summary = tool_use.input.get("summary", "Consolidated memory.")
            
            # 1. Create parent episode
            parent_episode = Episode(
                session_id=session_id,
                summary=summary,
                level=1,
                parent_episode_ids=[ep.id for ep in raw_episodes],
                decayed=False
            )
            db.add(parent_episode)
            
            # 2. Decay children
            for ep in raw_episodes:
                ep.decayed = True
                db.add(ep)
                
            db.commit()
            db.refresh(parent_episode)
            
            return {
                "status": "success",
                "message": f"Consolidated {len(raw_episodes)} episodes.",
                "parent_id": str(parent_episode.id),
                "summary": summary
            }
    except Exception as e:
        print(f"Error during consolidation: {e}")
        db.rollback()
        
    return {"status": "error", "message": "Failed to consolidate."}

def mock_consolidation(raw_episodes: List[Episode], session_id: str, db: Session):
    parent_episode = Episode(
        session_id=session_id,
        summary="User shared several details about their preferences and activities.",
        level=1,
        parent_episode_ids=[ep.id for ep in raw_episodes],
        decayed=False
    )
    db.add(parent_episode)
    
    for ep in raw_episodes:
        ep.decayed = True
        db.add(ep)
        
    db.commit()
    db.refresh(parent_episode)
    return {
        "status": "success",
        "message": f"Mock consolidated {len(raw_episodes)} episodes.",
        "parent_id": str(parent_episode.id),
        "summary": parent_episode.summary
    }
