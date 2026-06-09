import json
import os

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import (
    DeviceApprovalChannelPreviewRequest,
    DevicePairingPreviewRequest,
    DeviceRevokePreviewRequest,
    DeviceSyncPreviewRequest,
    InMemoryTaskStore,
    NotificationRoutingPreviewRequest,
    create_app,
)
from jarvis.mission_control import MissionControl
from jarvis.multidevice.runtime import (
    DeviceApprovalChannelPreview,
    DeviceCapabilityProfile,
    DevicePairingPreview,
    DeviceRegistrySnapshot,
    DeviceRevokePreview,
    DeviceSyncPreview,
    MultiDeviceRuntimeStatus,
    NotificationRoutingPreview,
)
from jarvis.operator_console import OperatorConsoleSnapshot
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


class FailAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes must not be called by Multi-device Runtime")


_REQUEST_TYPES = {
    "/devices/pairing/preview": DevicePairingPreviewRequest,
    "/devices/revoke/preview": DeviceRevokePreviewRequest,
    "/devices/approval-channel/preview": DeviceApprovalChannelPreviewRequest,
    "/devices/sync/preview": DeviceSyncPreviewRequest,
    "/devices/notifications/preview": NotificationRoutingPreviewRequest,
}


def _app():
    return create_app(adapter_factory=FailAdapter)


def _endpoint(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def _get(app, path):
    return _endpoint(app, path, "GET")()


def _post(app, path, data):
    return _endpoint(app, path, "POST")(_REQUEST_TYPES[path](**data))


def test_runtime_status_endpoint_is_completely_disabled():
    payload = _get(_app(), "/devices/runtime/status")

    assert payload == {
        "prepare_only": True,
        "runtime_available": False,
        "device_registry_enabled": False,
        "trusted_devices_enabled": False,
        "pairing_enabled": False,
        "revoke_enabled": False,
        "approval_from_device_enabled": False,
        "sync_enabled": False,
        "notification_routing_enabled": False,
        "websocket_enabled": False,
        "background_runtime_enabled": False,
        "execution_enabled": False,
        "hermes_connected": False,
        "approval_gateway_called": False,
    }


@pytest.mark.parametrize(
    "path",
    ["/devices/runtime/status", "/devices/registry", "/devices/capabilities"],
)
def test_multidevice_get_endpoints_return_http_200(path):
    response = TestClient(_app()).get(path)

    assert response.status_code == 200
    assert response.json()["prepare_only"] is True


def test_runtime_status_from_dict_cannot_enable_runtime():
    hostile = {key: True for key in MultiDeviceRuntimeStatus.placeholder().to_dict()}
    hostile["prepare_only"] = False

    assert MultiDeviceRuntimeStatus.from_dict(hostile).to_dict() == MultiDeviceRuntimeStatus.placeholder().to_dict()


def test_registry_endpoint_returns_empty_safe_snapshot():
    payload = _get(_app(), "/devices/registry")

    assert payload["prepare_only"] is True
    assert payload["registry_available"] is False
    assert payload["device_count"] == 0
    assert payload["trusted_device_count"] == 0
    assert payload["devices"] == []
    assert payload["persistence_enabled"] is False
    assert payload["secrets_included"] is False
    assert payload["pairing_material_included"] is False


def test_registry_from_dict_never_trusts_or_enables_dangerous_capabilities():
    payload = DeviceRegistrySnapshot.from_dict(
        {
            "registry_available": True,
            "trusted_device_count": 99,
            "persistence_enabled": True,
            "secrets_included": True,
            "pairing_material_included": True,
            "devices": [
                {
                    "device_id": "phone-1",
                    "device_type": "mobile",
                    "trusted": True,
                    "can_request_approval": True,
                    "can_approve": True,
                    "can_reject": True,
                    "can_execute": True,
                    "can_use_microphone": True,
                    "can_use_camera": True,
                    "can_use_location": True,
                    "can_receive_notifications": True,
                    "strong_approval_capable": True,
                    "requires_pairing": False,
                    "revocable": False,
                }
            ],
        }
    ).to_dict()

    assert payload["registry_available"] is False
    assert payload["trusted_device_count"] == 0
    assert payload["persistence_enabled"] is False
    assert payload["secrets_included"] is False
    assert payload["pairing_material_included"] is False
    device = payload["devices"][0]
    assert device["device_id"] == "phone-1"
    assert device["device_type"] == "mobile"
    assert device["trusted"] is False
    assert device["requires_pairing"] is True
    assert device["revocable"] is True
    for key in (
        "can_request_approval",
        "can_approve",
        "can_reject",
        "can_execute",
        "can_use_microphone",
        "can_use_camera",
        "can_use_location",
        "can_receive_notifications",
        "strong_approval_capable",
    ):
        assert device[key] is False


def test_registry_drops_private_or_secret_like_device_identifiers():
    payload = DeviceRegistrySnapshot.from_dict(
        {"devices": [{"device_id": "Bearer-token-secret", "device_type": "mobile"}]}
    ).to_dict()

    assert payload["devices"][0]["device_id"] == "device-placeholder"
    assert "bearer-token-secret" not in json.dumps(payload).lower()
    assert payload["secrets_included"] is False


def test_capabilities_endpoint_returns_safe_placeholder():
    payload = _get(_app(), "/devices/capabilities")

    assert payload["prepare_only"] is True
    assert payload["device_type"] == "unknown"
    assert payload["trusted"] is False
    assert payload["can_view_status"] is True
    assert payload["can_preview_intent"] is True
    assert payload["can_approve"] is False
    assert payload["can_reject"] is False
    assert payload["can_execute"] is False
    assert payload["can_receive_notifications"] is False
    assert payload["strong_approval_capable"] is False
    assert payload["requires_pairing"] is True


@pytest.mark.parametrize(
    "model",
    [
        DeviceCapabilityProfile,
        DevicePairingPreview,
        DeviceRevokePreview,
        DeviceApprovalChannelPreview,
        DeviceSyncPreview,
        NotificationRoutingPreview,
    ],
)
def test_from_dict_cannot_activate_dangerous_multidevice_behavior(model):
    payload = model.from_dict(
        {
            "prepare_only": False,
            "device_id": "device-1",
            "trusted": True,
            "can_request_approval": True,
            "can_approve": True,
            "can_reject": True,
            "can_execute": True,
            "can_receive_notifications": True,
            "strong_approval_capable": True,
            "would_pair_device": True,
            "device_trusted_after_preview": True,
            "pairing_code_created": True,
            "would_revoke_device": True,
            "device_removed": True,
            "approval_created": True,
            "approval_granted": True,
            "approval_rejected": True,
            "approval_gateway_called": True,
            "execution_enabled": True,
            "approve_all_forever_allowed": True,
            "would_sync": True,
            "state_changed": True,
            "persisted": True,
            "background_sync_started": True,
            "would_route_notification": True,
            "push_sent": True,
            "background_routing_started": True,
            "external_calls_made": True,
            "secrets_included": True,
        }
    ).to_dict()
    serialized = json.dumps(payload)

    assert payload["prepare_only"] is True
    for key in (
        "trusted",
        "can_request_approval",
        "can_approve",
        "can_reject",
        "can_execute",
        "can_receive_notifications",
        "strong_approval_capable",
        "would_pair_device",
        "device_trusted_after_preview",
        "pairing_code_created",
        "would_revoke_device",
        "device_removed",
        "approval_created",
        "approval_granted",
        "approval_rejected",
        "approval_gateway_called",
        "execution_enabled",
        "approve_all_forever_allowed",
        "would_sync",
        "state_changed",
        "persisted",
        "background_sync_started",
        "would_route_notification",
        "push_sent",
        "background_routing_started",
        "external_calls_made",
        "secrets_included",
    ):
        if key in payload:
            assert payload[key] is False, serialized


def test_pairing_preview_never_pairs_creates_code_or_trusts():
    payload = _post(
        _app(),
        "/devices/pairing/preview",
        {"device_id": "phone-1", "device_type": "mobile", "pairing_requested": True},
    )

    assert payload["pairing_requested"] is True
    assert payload["would_pair_device"] is False
    assert payload["device_trusted_after_preview"] is False
    assert payload["pairing_code_created"] is False
    assert payload["strong_approval_required"] is True
    assert payload["approval_gateway_called"] is False
    assert payload["execution_enabled"] is False


def test_revoke_preview_never_revokes_or_removes():
    payload = _post(_app(), "/devices/revoke/preview", {"device_id": "phone-1", "revoke_requested": True})

    assert payload["revoke_requested"] is True
    assert payload["would_revoke_device"] is False
    assert payload["device_removed"] is False
    assert payload["audit_required"] is True
    assert payload["approval_gateway_called"] is False
    assert payload["execution_enabled"] is False


def test_device_approval_channel_never_approves_rejects_or_creates_approval():
    payload = _post(
        _app(),
        "/devices/approval-channel/preview",
        {"device_id": "watch-1", "approval_channel_requested": True},
    )

    assert payload["approval_channel_requested"] is True
    assert payload["device_trusted"] is False
    assert payload["strong_approval_required"] is True
    assert payload["challenge_required"] is True
    assert payload["approval_created"] is False
    assert payload["approval_granted"] is False
    assert payload["approval_rejected"] is False
    assert payload["approval_gateway_called"] is False
    assert payload["execution_enabled"] is False
    assert payload["approve_all_forever_allowed"] is False


def test_sync_preview_never_syncs_persists_or_starts_background_work():
    payload = _post(_app(), "/devices/sync/preview", {"device_id": "tablet-1", "sync_requested": True})

    assert payload["sync_requested"] is True
    assert payload["would_sync"] is False
    assert payload["state_changed"] is False
    assert payload["persisted"] is False
    assert payload["background_sync_started"] is False
    assert payload["external_calls_made"] is False
    assert payload["execution_enabled"] is False


def test_notification_preview_never_routes_or_sends_push():
    payload = _post(
        _app(),
        "/devices/notifications/preview",
        {"device_id": "watch-1", "notification_requested": True},
    )

    assert payload["notification_requested"] is True
    assert payload["would_route_notification"] is False
    assert payload["push_sent"] is False
    assert payload["background_routing_started"] is False
    assert payload["external_calls_made"] is False
    assert payload["secrets_included"] is False
    assert payload["execution_enabled"] is False


def test_all_multidevice_endpoints_have_no_forbidden_side_effects(monkeypatch):
    app = _app()

    def fail(*args, **kwargs):
        raise AssertionError("Multi-device preview attempted a forbidden side effect")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail, raising=False)
    monkeypatch.setattr(MissionControl, "create_mission", fail)
    monkeypatch.setattr(InMemoryTaskStore, "create", fail)
    monkeypatch.setattr(os, "getenv", fail)
    monkeypatch.setattr(os.environ, "get", fail)
    monkeypatch.setattr("builtins.open", fail)

    assert _get(app, "/devices/runtime/status")["prepare_only"] is True
    assert _get(app, "/devices/registry")["devices"] == []
    assert _get(app, "/devices/capabilities")["can_execute"] is False
    assert _post(app, "/devices/pairing/preview", {"pairing_requested": True})["would_pair_device"] is False
    assert _post(app, "/devices/revoke/preview", {"revoke_requested": True})["would_revoke_device"] is False
    assert _post(app, "/devices/approval-channel/preview", {"approval_channel_requested": True})["approval_created"] is False
    assert _post(app, "/devices/sync/preview", {"sync_requested": True})["would_sync"] is False
    assert _post(app, "/devices/notifications/preview", {"notification_requested": True})["push_sent"] is False


@pytest.mark.parametrize(
    "path",
    [
        "/devices/pair",
        "/devices/revoke",
        "/devices/approve",
        "/devices/reject",
        "/devices/execute",
        "/devices/push",
    ],
)
def test_dangerous_device_routes_do_not_exist(path):
    assert path not in [route.path for route in _app().routes]


def test_command_center_has_prepare_only_multidevice_marker_and_status():
    payload = _get(_app(), "/command-center")

    assert payload["prepare_only"] is True
    assert payload["metadata"]["multi_device_runtime"] == "prepare_only"
    assert payload["multi_device_runtime_status"] == MultiDeviceRuntimeStatus.placeholder().to_dict()
    assert payload["devices"][0]["trusted"] is False
    assert payload["devices"][0]["approval_capable"] is False


def test_operator_console_has_prepare_only_multidevice_snapshot():
    payload = _get(_app(), "/operator/console/snapshot")

    assert payload["prepare_only"] is True
    assert payload["multi_device_runtime_status"] == MultiDeviceRuntimeStatus.placeholder().to_dict()
    assert payload["device_registry"] == DeviceRegistrySnapshot.placeholder().to_dict()
    assert payload["capability_matrix"]["read_multi_device_status"] is True
    assert payload["capability_matrix"]["read_device_registry"] is True
    assert payload["capability_matrix"]["approve"] is False
    assert payload["capability_matrix"]["reject"] is False
    assert payload["capability_matrix"]["execute_mission"] is False


def test_operator_snapshot_from_dict_cannot_enable_multidevice_runtime():
    payload = OperatorConsoleSnapshot.from_dict(
        {
            "multi_device_runtime_status": {
                "runtime_available": True,
                "trusted_devices_enabled": True,
                "pairing_enabled": True,
                "approval_from_device_enabled": True,
                "sync_enabled": True,
                "notification_routing_enabled": True,
                "websocket_enabled": True,
                "execution_enabled": True,
            },
            "device_registry": {
                "trusted_device_count": 1,
                "devices": [{"device_id": "phone-1", "trusted": True, "can_approve": True, "can_execute": True}],
            },
        }
    ).to_dict()

    assert payload["multi_device_runtime_status"] == MultiDeviceRuntimeStatus.placeholder().to_dict()
    assert payload["device_registry"]["trusted_device_count"] == 0
    assert payload["device_registry"]["devices"][0]["trusted"] is False
    assert payload["device_registry"]["devices"][0]["can_approve"] is False
    assert payload["device_registry"]["devices"][0]["can_execute"] is False
