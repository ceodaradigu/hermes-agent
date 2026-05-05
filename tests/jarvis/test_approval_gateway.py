import pytest

from jarvis.policy.approval_gateway import ApprovalGateway, ApprovalStatus


def test_approve_pending_request_works():
    gateway = ApprovalGateway()
    req = gateway.create_request("leer .env", rationale="debug")

    approved = gateway.approve(req.request_id, note="Aprobado")
    assert approved.status == ApprovalStatus.APPROVED
    assert approved.decided_at is not None


def test_reject_pending_request_works():
    gateway = ApprovalGateway()
    req = gateway.create_request("lanzar campañas de pago", rationale="growth")

    rejected = gateway.reject(req.request_id, note="No")
    assert rejected.status == ApprovalStatus.REJECTED
    assert rejected.decided_at is not None


def test_approve_then_reject_raises_value_error():
    gateway = ApprovalGateway()
    req = gateway.create_request("publicar en producción")

    gateway.approve(req.request_id)
    with pytest.raises(ValueError):
        gateway.reject(req.request_id)


def test_reject_then_approve_raises_value_error():
    gateway = ApprovalGateway()
    req = gateway.create_request("borrar archivos")

    gateway.reject(req.request_id)
    with pytest.raises(ValueError):
        gateway.approve(req.request_id)


def test_create_request_with_empty_action_raises_value_error():
    gateway = ApprovalGateway()
    with pytest.raises(ValueError):
        gateway.create_request("   ")


def test_get_nonexistent_request_raises_key_error():
    gateway = ApprovalGateway()
    with pytest.raises(KeyError):
        gateway.get_request("missing-id")


def test_list_requests_returns_created_requests():
    gateway = ApprovalGateway()
    req1 = gateway.create_request("leer .env")
    req2 = gateway.create_request("instalar paquetes")

    requests = gateway.list_requests()
    ids = {r.request_id for r in requests}
    assert ids == {req1.request_id, req2.request_id}
