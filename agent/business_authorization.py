"""Business Authorization Module - D4 Implementation

Authorizes business-level operations based on worker identity and tenant scope.

This module provides a centralized authorization service that operates between
the orchestrator and execution engine, ensuring business isolation while respecting
the frozen constraints of the existing architecture.
"""

from typing import Optional, Tuple
import logging

from .worker_registry import WorkerRegistry
from .worker_contracts import WorkerLivenessState

logger = logging.getLogger(__name__)

_registry = WorkerRegistry()


class BusinessAuthorization:
    """Centralized business authorization service."""

    def authorize(
        self,
        business_id: str,
        tenant_scope: Optional[str] = None,
        worker_id: str = "",
        worker_epoch: int = 0,
    ) -> Tuple[bool, str]:
        if not business_id:
            logger.error("Authorization failed: missing business_id")
            return False, "missing_business_id"

        if not worker_id:
            logger.error("Authorization failed: missing worker_id")
            return False, "missing_worker_id"

        if worker_epoch <= 0:
            logger.error("Authorization failed: invalid worker_epoch")
            return False, "invalid_worker_epoch"

        worker_entry = _registry.get(worker_id, tenant_scope=tenant_scope)

        if not worker_entry:
            logger.error("Authorization failed: worker %s not found", worker_id)
            return False, "worker_not_found"

        if worker_entry["state"] != WorkerLivenessState.LIVE.value:
            logger.error(
                "Authorization failed: worker %s is not LIVE (state: %s)",
                worker_id, worker_entry["state"],
            )
            return False, f"worker_{worker_id}_state_{worker_entry['state']}"

        if tenant_scope is not None:
            tenant_scopes = worker_entry.get("identity", {}).get("tenant_scope", [])
            if tenant_scope not in tenant_scopes:
                logger.error(
                    "Authorization failed: worker %s not in tenant scope %s",
                    worker_id, tenant_scope,
                )
                return False, f"tenant_mismatch: expected {tenant_scope}, got {tenant_scopes}"

        logger.info(
            "Authorization granted for business=%s, worker=%s",
            business_id, worker_id,
        )
        return True, "authorized"


def get_authorization_service() -> BusinessAuthorization:
    """Factory function to get the authorization service instance."""
    return BusinessAuthorization()
