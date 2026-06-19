from __future__ import annotations

from typing import Any, Dict, List

from jarvis.memory_brain_v2 import MemoryBrainV2Store


MEMORY_BRAIN_V3_SCHEMA_VERSION = "jarvis.memory_brain_v3.v1"


class MemoryBrainV3:
    """Useful memory runtime wrapper over Memory Brain v2.

    V3 adds review, compaction, and influence read models. It deliberately does
    not grant permissions, autoload memories, call LLMs, or index secrets.
    """

    def __init__(self, store: MemoryBrainV2Store) -> None:
        self.store = store

    def status(self) -> Dict[str, Any]:
        v2_status = self.store.status()
        counts = dict(v2_status.get("counts") or {})
        return {
            "schema_version": MEMORY_BRAIN_V3_SCHEMA_VERSION,
            "state": {
                "mode": "controlled_useful_memory_runtime_v3",
                "available": True,
                "backing_store_schema": v2_status.get("schema_version"),
                "persistent": bool(v2_status.get("state", {}).get("persistent", False)),
                "local_only": True,
                "review_required": True,
                "compaction_preview_available": True,
                "influence_explanation_available": True,
                "memory_autoload_enabled": False,
                "memory_auto_activation_enabled": False,
                "memory_grants_permission": False,
            },
            "counts": counts,
            "supported_memory_types": [
                "entity",
                "project",
                "decision",
                "preference",
                "fact",
                "contradiction",
            ],
            "review_controls": {
                "create_update_review_forget_delete": True,
                "contradiction_handling": True,
                "provenance_required": True,
                "confidence_required": True,
                "sensitivity_required": True,
                "why_i_remember_this": True,
                "why_this_influenced": True,
            },
            "safety": {
                "memory_never_grants_permission": True,
                "memory_never_downgrades_risk": True,
                "secret_indexing_default": False,
                "sensitive_autosave": False,
                "external_llm": False,
                "cloud_memory": False,
                "hermes_dispatch_allowed": False,
            },
            "source_endpoint": "/mark-3/memory-brain-v3/status",
            "metadata_only": True,
            "read_only": True,
        }

    def review(self, *, limit: int = 25) -> Dict[str, Any]:
        memories = self.store.list_memories(limit=limit)
        return {
            "schema_version": MEMORY_BRAIN_V3_SCHEMA_VERSION,
            "memories": memories,
            "pending_review": [item for item in memories if item.get("review_required")],
            "active": [item for item in memories if item.get("active") and not item.get("forgotten") and not item.get("deleted")],
            "forgotten_deleted": [item for item in memories if item.get("forgotten") or item.get("deleted")],
            "permission_effect": self.store.permission_effect(),
            "metadata_only": True,
            "read_only": True,
            "source_endpoint": "/mark-3/memory-brain-v3/review",
        }

    def compaction_preview(self, *, limit: int = 50) -> Dict[str, Any]:
        memories = self.store.list_memories(limit=limit)
        active = [item for item in memories if item.get("active") and not item.get("forgotten") and not item.get("deleted")]
        pending = [item for item in memories if item.get("review_required")]
        contradictions = [item for item in memories if item.get("memory_type") == "contradiction"]
        summary_items = [
            {
                "memory_id": item["memory_id"],
                "memory_type": item["memory_type"],
                "entity_name": item["entity_name"],
                "content_summary": item["content_summary"],
                "confidence": item["confidence"],
                "sensitivity": item["sensitivity"],
                "provenance": item["provenance"],
                "reason_to_remember": item["reason_to_remember"],
            }
            for item in active[:12]
        ]
        return {
            "schema_version": MEMORY_BRAIN_V3_SCHEMA_VERSION,
            "status": "preview_only_not_applied",
            "summary_preview": summary_items,
            "counts": {
                "input_memories": len(memories),
                "active_included": len(summary_items),
                "pending_review_excluded": len(pending),
                "contradictions": len(contradictions),
            },
            "rules": {
                "operator_review_required_before_apply": True,
                "secrets_excluded": True,
                "forgotten_deleted_excluded": True,
                "permission_effect": "none",
                "risk_downgrade_allowed": False,
            },
            "metadata_only": True,
            "read_only": True,
            "source_endpoint": "/mark-3/memory-brain-v3/compaction-preview",
        }

    def influence_explanation(self, memory_id: str | None = None) -> Dict[str, Any]:
        if memory_id:
            why = self.store.why_used(memory_id)
            remember = self.store.why_remember(memory_id)
            return {
                "schema_version": MEMORY_BRAIN_V3_SCHEMA_VERSION,
                "memory_id": memory_id,
                "why_used": why,
                "why_remember": remember,
                "permission_effect": self.store.permission_effect(memory_id),
                "metadata_only": True,
                "read_only": True,
            }
        active = [
            item
            for item in self.store.list_memories(limit=50)
            if item.get("active") and not item.get("forgotten") and not item.get("deleted")
        ]
        return {
            "schema_version": MEMORY_BRAIN_V3_SCHEMA_VERSION,
            "active_memory_count": len(active),
            "influences": [_memory_influence(item) for item in active[:10]],
            "permission_effect": self.store.permission_effect(),
            "metadata_only": True,
            "read_only": True,
            "source_endpoint": "/mark-3/memory-brain-v3/influence",
        }


def _memory_influence(memory: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "memory_id": memory.get("memory_id"),
        "memory_type": memory.get("memory_type"),
        "entity_name": memory.get("entity_name"),
        "influence_summary": memory.get("influence_summary"),
        "why_used": memory.get("why_used"),
        "confidence": memory.get("confidence"),
        "sensitivity": memory.get("sensitivity"),
        "used_for_permission": False,
        "risk_downgrade_allowed": False,
    }
