from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class HermesAdapterConfig:
    """Configuration for creating internal Hermes runtime sessions."""

    model: str = ""
    max_iterations: int = 90
    enabled_toolsets: Optional[List[str]] = None
    disabled_toolsets: Optional[List[str]] = None
    quiet_mode: bool = True
    platform: str = "jarvis"


class HermesRuntimeAdapter:
    """Thin wrapper over AIAgent for internal JARVIS orchestration."""

    def __init__(self, config: Optional[HermesAdapterConfig] = None):
        self.config = config or HermesAdapterConfig()

    def create_agent(self, session_id: Optional[str] = None) -> AIAgent:
        from run_agent import AIAgent

        return AIAgent(
            model=self.config.model,
            max_iterations=self.config.max_iterations,
            enabled_toolsets=self.config.enabled_toolsets,
            disabled_toolsets=self.config.disabled_toolsets,
            quiet_mode=self.config.quiet_mode,
            platform=self.config.platform,
            session_id=session_id,
        )

    def run(
        self,
        message: str,
        *,
        session_id: Optional[str] = None,
        system_message: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        agent = self.create_agent(session_id=session_id)
        return agent.run_conversation(
            user_message=message,
            system_message=system_message,
            conversation_history=conversation_history,
            task_id=task_id,
        )
