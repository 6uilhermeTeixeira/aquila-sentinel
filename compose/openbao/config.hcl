ui = true
storage "raft" {
  path    = "/openbao/data"
  node_id = "sentinel-1"
}
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true
}
api_addr     = "http://127.0.0.1:8200"
cluster_addr = "http://127.0.0.1:8201"
audit "file" "file" {
  options {
    file_path = "/openbao/audit/audit.log"
    mode = "0600"
  }
}
