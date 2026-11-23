package sentinel.access
import rego.v1

default allow := false

allow if {
  input.subject.verified == true
  input.subject.expires_at > time.now_ns() / 1000000000
  input.resource != ""
  input.action != ""
  data.sentinel.permissions[input.subject.id][input.resource][input.action] == true
}
