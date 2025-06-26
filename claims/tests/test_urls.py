from django.urls import resolve
from claims.api.v1.views import CantClaimHVView


def test_cant_claim_hv_url():
    match = resolve('/api/v1/cant-claim-hv')
    assert match.func.view_class is CantClaimHVView
