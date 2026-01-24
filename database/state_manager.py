"""
State Manager for the Autonomous Silver Prediction Agent.
Manages agent state and session tracking.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class AgentState:
    """Represents the current state of the agent."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_step: str = "idle"
    last_collection_time: Optional[datetime] = None
    last_prediction_time: Optional[datetime] = None
    collected_data_count: int = 0
    predictions_made: int = 0
    errors_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateManager:
    """
    Manages the agent's state throughout its lifecycle.
    Integrates with the database for persistence.
    """
    
    def __init__(self, db_client=None):
        """
        Initialize the state manager.
        
        Args:
            db_client: Optional SupabaseClient for persistence.
        """
        self.db_client = db_client
        self.state = AgentState()
        self._state_history: list = []
    
    @property
    def session_id(self) -> str:
        """Get the current session ID."""
        return self.state.session_id
    
    def new_session(self) -> str:
        """Start a new agent session."""
        self.state = AgentState()
        return self.state.session_id
    
    def update_step(self, step: str) -> None:
        """
        Update the current step of the agent.
        
        Args:
            step: The new step name (e.g., 'collecting', 'analyzing', 'predicting')
        """
        self._state_history.append({
            "step": self.state.current_step,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.state.current_step = step
    
    def record_collection(self) -> None:
        """Record a successful data collection."""
        self.state.last_collection_time = datetime.utcnow()
        self.state.collected_data_count += 1
    
    def record_prediction(self) -> None:
        """Record a prediction made by the agent."""
        self.state.last_prediction_time = datetime.utcnow()
        self.state.predictions_made += 1
    
    def record_error(self) -> None:
        """Record an error occurrence."""
        self.state.errors_count += 1
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the current state."""
        return {
            "session_id": self.state.session_id,
            "current_step": self.state.current_step,
            "last_collection": self.state.last_collection_time.isoformat() 
                if self.state.last_collection_time else None,
            "last_prediction": self.state.last_prediction_time.isoformat() 
                if self.state.last_prediction_time else None,
            "collections": self.state.collected_data_count,
            "predictions": self.state.predictions_made,
            "errors": self.state.errors_count,
            "steps_taken": len(self._state_history)
        }
    
    def log_to_database(self, log_type: str, data: Dict[str, Any]) -> None:
        """
        Persist a log entry to the database.
        
        Args:
            log_type: Type of log ('reasoning', 'decision', 'action', 'error', 'prediction')
            data: Log data to persist.
        """
        if self.db_client is None:
            return
        
        log_entry = {
            "session_id": self.state.session_id,
            "log_type": log_type,
            "agent_state": self.state.current_step,
            **data
        }
        
        self.db_client.log_agent_action(log_entry)
