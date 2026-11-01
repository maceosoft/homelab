terraform {
  required_providers {
    incus = {
      source  = "lxc/incus"
      version = "~> 1.2"
    }
  }
}

provider "incus" {
  remote {
    name    = "homelab"
    address = var.incus_remote_address
  }
}
