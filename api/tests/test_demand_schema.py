from pydantic import ValidationError

from app.schemas.demand import OrchestrateRequest


def test_orchestrate_request_accepts_oci_provider():
    payload = OrchestrateRequest(provider="oci")

    assert payload.provider == "oci"


def test_orchestrate_request_rejects_unknown_provider():
    try:
        OrchestrateRequest(provider="digitalocean")
    except ValidationError:
        return

    raise AssertionError("unknown provider should be rejected")
