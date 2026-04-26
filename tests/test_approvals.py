import pytest

from jinguzhou.approvals.tokens import ApprovalTokenManager


def test_approval_token_allows_matching_review_decision() -> None:
    manager = ApprovalTokenManager("secret")
    token = manager.issue(
        request_id="req-1",
        stage="tool",
        rule_ids=["rule-a"],
        approver="alice",
    )

    claims = manager.allows(
        token,
        request_id="req-1",
        stage="tool",
        rule_ids=["rule-a"],
    )

    assert claims.approver == "alice"


def test_approval_token_rejects_mismatched_request() -> None:
    manager = ApprovalTokenManager("secret")
    token = manager.issue(request_id="req-1", stage="tool", rule_ids=["rule-a"])

    with pytest.raises(ValueError):
        manager.allows(token, request_id="req-2", stage="tool", rule_ids=["rule-a"])
