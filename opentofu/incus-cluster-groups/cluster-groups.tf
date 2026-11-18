resource "incus_cluster_group" "x86_nodes" {
  name        = "x86-nodes"
  description = "x86: invincible (M920q), oliver (M700) y eve (MacBook Pro T2)"
}

resource "incus_cluster_group" "arm64_nodes" {
  name        = "arm64-nodes"
  description = "Orange Pi 5 Plus (deborah)"
}
