from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class HermesAdapterConfig:
    """Configuration for creating internal Hermes runtime sessions."""

    model: str = ""
    max_iterations: int = 90
    enabled_toolsets: Optional[List[str]] = None
    disabled_toolsets: Optional[List[str]] = None
    quiet_mode: bool = True
    platform: str = "jarvis"
    allowed_tools: Optional[List[str]] = None
    tool_guard: Optional[Callable[[str, Dict[str, Any]], Any]] = None
    skip_context_files: bool = False
    skip_memory: bool = False
    governed_mode: bool = False
    disable_memory_provider_tools: bool = False
    disable_context_engine: bool = False
    disable_plugins: bool = False
    disable_delegate_task: bool = False
    disable_mcp: bool = False


class HermesRuntimeAdapter:
    """Thin wrapper over AIAgent for internal JARVIS orchestration."""

    def __init__(self, config: Optional[HermesAdapterConfig] = None):
        self.config = config or HermesAdapterConfig()
        self.last_agent: Any = None
        self._pending_interrupt_reason: Optional[str] = None
        self._interrupt_delivery_callback: Optional[Callable[[], None]] = None

    def set_interrupt_delivery_callback(self, callback: Callable[[], None]) -> None:
        self._interrupt_delivery_callback = callback

    def interrupt(self, reason: str) -> bool:
        agent = self.last_agent
        if agent and hasattr(agent, "interrupt"):
            agent.interrupt(reason)
            self._pending_interrupt_reason = None
            if self._interrupt_delivery_callback:
                self._interrupt_delivery_callback()
            return True
        self._pending_interrupt_reason = reason
        return False

    def create_agent(self, session_id: Optional[str] = None) -> AIAgent:
        from run_agent import AIAgent

        agent = AIAgent(
            model=self.config.model,
            max_iterations=self.config.max_iterations,
            enabled_toolsets=self.config.enabled_toolsets,
            disabled_toolsets=self.config.disabled_toolsets,
            quiet_mode=self.config.quiet_mode,
            platform=self.config.platform,
            session_id=session_id,
            allowed_tools=self.config.allowed_tools,
            tool_guard=self.config.tool_guard,
            skip_context_files=self.config.skip_context_files,
            skip_memory=self.config.skip_memory,
            governed_mode=self.config.governed_mode,
            disable_memory_provider_tools=self.config.disable_memory_provider_tools,
            disable_context_engine=self.config.disable_context_engine,
            disable_plugins=self.config.disable_plugins,
            disable_delegate_task=self.config.disable_delegate_task,
            disable_mcp=self.config.disable_mcp,
        )
        self.last_agent = agent
        if self._pending_interrupt_reason and hasattr(agent, "interrupt"):
            reason = self._pending_interrupt_reason
            self._pending_interrupt_reason = None
            agent.interrupt(reason)
            if self._interrupt_delivery_callback:
                self._interrupt_delivery_callback()
        return agent

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
