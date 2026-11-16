terraform {
  required_providers {
    incus = {
      source  = "lxc/incus"
      version = "~> 1.2"
    }
  }
}

# Configuración del provider 1.x (lxc/terraform-provider-incus#254): el remoto por defecto se elige con
# default_remote y address es la URL completa. Sin default_remote, los recursos usarían el remoto por defecto
# del cliente incus local (normalmente "local", el socket unix), no el clúster.
provider "incus" {
  default_remote = "homelab"

  remote {
    name    = "homelab"
    address = var.incus_remote_address
  }
}
