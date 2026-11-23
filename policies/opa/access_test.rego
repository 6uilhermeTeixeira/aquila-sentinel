package sentinel.access_test
import rego.v1

valid_subject := {"id": "pipeline-1", "verified": true, "expires_at": 9999999999}
permission := {"pipeline-1": {"reports": {"read": true}}}

test_explicit_grant if {
    data.sentinel.access.allow with input as {"subject": valid_subject, "resource": "reports", "action": "read"} with data.sentinel.permissions as permission
}

test_anonymous_denied if {
    not data.sentinel.access.allow with input as {"subject": {"id": "pipeline-1", "verified": false, "expires_at": 9999999999}, "resource": "reports", "action": "read"} with data.sentinel.permissions as permission
}

test_expired_denied if {
    not data.sentinel.access.allow with input as {"subject": {"id": "pipeline-1", "verified": true, "expires_at": 1}, "resource": "reports", "action": "read"} with data.sentinel.permissions as permission
}

test_missing_grant_denied if {
    not data.sentinel.access.allow with input as {"subject": valid_subject, "resource": "secrets", "action": "read"} with data.sentinel.permissions as permission
}
