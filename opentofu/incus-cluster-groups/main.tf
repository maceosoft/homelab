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
#
# Autenticación: la del cliente incus de tu equipo (config_dir). Con authentication_type = "oidc" usa tu login SSO
# (Dex/GitHub) guardado por `incus remote add homelab … --auth-type=oidc`; con "tls", el certificado de cliente
# client.crt/client.key de esa carpeta. Ver ../README.md.
provider "incus" {
  config_dir     = var.incus_config_dir
  default_remote = "homelab"

  remote {
    name                = "homelab"
    address             = var.incus_remote_address
    authentication_type = var.incus_authentication_type
  }
}
