from datetime import datetime, timedelta, timezone

from jarvis.phase_5_local_controller_trusted_identity_voice_approval import Phase5IdentityStore


def test_trusted_device_persistence_and_revocation_survives_restart(tmp_path):
    store = Phase5IdentityStore(base_dir=tmp_path)
    device = store.upsert_trusted_device(
        device_id="device-test",
        display_name="David phone",
        channel_type="local_pairing",
        public_identifier="phone-public-id",
        fingerprint_material="phone-fingerprint-material",
        capabilities={"can_grant_normal": True, "voice_approval": True},
        approval_scope=["voice_approval", "normal"],
        metadata={"note": "safe metadata", "token": "SHOULD_REDACT"},
        trust_source="local_pairing_challenge",
    )
    assert device["trusted"] is True
    assert device["public_identifier_hash"] != "phone-public-id"
    assert device["fingerprint_hash"] != "phone-fingerprint-material"
    assert device["metadata"]["token"] == "[redacted]"

    revoked = store.revoke_device("device-test", reason="lost")
    assert revoked["revoked"] is True
    store.close()

    restarted = Phase5IdentityStore(base_dir=tmp_path)
    persisted = restarted.get_device("device-test")
    assert persisted["revoked"] is True
    assert persisted["trusted"] is False
    assert persisted["revocation_reason"] == "lost"

    attempted_retrust = restarted.upsert_trusted_device(
        device_id="device-test",
        display_name="David phone",
        channel_type="local_pairing",
        public_identifier="phone-public-id",
        fingerprint_material="phone-fingerprint-material",
        capabilities={"can_grant_normal": True, "voice_approval": True},
        approval_scope=["voice_approval", "normal"],
        trust_source="local_pairing_challenge",
    )
    assert attempted_retrust["revoked"] is True
    assert attempted_retrust["trusted"] is False


def test_pairing_challenge_one_time_expiry_scope_and_rate_limit(tmp_path):
    store = Phase5IdentityStore(base_dir=tmp_path)
    challenge = store.create_pairing_challenge(
        display_name="David phone",
        public_identifier="phone-public-id",
        channel="local_voice_device",
        scope=["voice_approval", "normal"],
    )

    wrong = store.verify_pairing_challenge(
        challenge_id=challenge["challenge_id"],
        nonce=challenge["nonce"],
        response_phrase="WRONG",
        public_identifier="phone-public-id",
        display_name="David phone",
        scope=["voice_approval", "normal"],
    )
    assert wrong["pairing_status"] == "rejected"
    assert wrong["trusted_device_created"] is False

    paired = store.verify_pairing_challenge(
        challenge_id=challenge["challenge_id"],
        nonce=challenge["nonce"],
        response_phrase=challenge["challenge_phrase"],
        public_identifier="phone-public-id",
        display_name="David phone",
        scope=["voice_approval", "normal"],
    )
    assert paired["pairing_status"] == "trusted_device_bound"
    assert paired["one_time_use_consumed"] is True
    assert paired["device"]["trusted"] is True
    assert paired["remote_execution_allowed"] is False

    replay = store.verify_pairing_challenge(
        challenge_id=challenge["challenge_id"],
        nonce=challenge["nonce"],
        response_phrase=challenge["challenge_phrase"],
        public_identifier="phone-public-id",
        display_name="David phone",
        scope=["voice_approval", "normal"],
    )
    assert replay["reason"] == "pairing_challenge_already_used"
    consumed_status = store.pairing_status()["recent_challenges"][0]
    assert consumed_status["status"] == "consumed"

    limited = store.create_pairing_challenge(
        display_name="Tablet",
        public_identifier="tablet-public-id",
        channel="local_voice_device",
        scope=["voice_approval"],
    )
    for _ in range(3):
        result = store.verify_pairing_challenge(
            challenge_id=limited["challenge_id"],
            nonce=limited["nonce"],
            response_phrase="WRONG",
            public_identifier="tablet-public-id",
            display_name="Tablet",
            scope=["voice_approval"],
        )
    assert result["rate_limited"] is True

    expired = store.create_pairing_challenge(
        display_name="Expired",
        public_identifier="expired-public-id",
        channel="local_voice_device",
        scope=["voice_approval"],
    )
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    store._conn.execute("UPDATE pairing_challenges SET expires_at=? WHERE challenge_id=?", (past, expired["challenge_id"]))
    store._conn.commit()
    expired_result = store.verify_pairing_challenge(
        challenge_id=expired["challenge_id"],
        nonce=expired["nonce"],
        response_phrase=expired["challenge_phrase"],
        public_identifier="expired-public-id",
        display_name="Expired",
        scope=["voice_approval"],
    )
    assert expired_result["reason"] == "pairing_challenge_expired"
    expired_status = store.pairing_status()["recent_challenges"][0]
    assert expired_status["status"] == "expired"


def test_import_preview_cannot_create_trust_or_capability(tmp_path):
    store = Phase5IdentityStore(base_dir=tmp_path)
    preview = store.import_preview(
        {
            "device_id": "imported-phone",
            "trusted": True,
            "verified": True,
            "paired": True,
            "capabilities": {"voice_approval": True, "can_grant_triple": True},
        }
    )
    assert preview["import_status"] == "rejected_preview_only"
    assert preview["trusted"] is False
    assert preview["verified"] is False
    assert preview["paired"] is False
    assert preview["hermes_dispatch_allowed"] is False
    assert store.get_device("imported-phone") is None
