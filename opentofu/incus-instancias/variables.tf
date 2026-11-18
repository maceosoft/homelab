variable "incus_remote_address" {
  description = "Endpoint HTTPS de la API de Incus (nombre del líder del clúster en el DNS del HomeLab)"
  type        = string
  default     = "https://incus.homelab.local:8443"
}

variable "incus_config_dir" {
  description = "Carpeta de configuración del cliente incus (macOS: ~/Library/Application Support/incus; Linux: ~/.config/incus)"
  type        = string
  default     = null
}

variable "incus_authentication_type" {
  description = "oidc (login SSO de la persona) o tls (certificado de cliente, para pipelines)"
  type        = string
  default     = "oidc"
}

variable "prefix" {
  description = "Prefijo de los nombres de las instancias (quedan en el DNS como <prefix>-web.ovn.homelab.local)"
  type        = string
  default     = "tofu-demo"
}

variable "network" {
  description = "Red de Incus de las instancias (OVN aislada: se llega a ellas desde la LAN solo por el balanceador)"
  type        = string
  default     = "ovn-lan"
}

variable "web_target" {
  description = "Miembro del clúster de Incus donde corre el contenedor web"
  type        = string
  default     = "invincible"
}

variable "vm_target" {
  description = "Miembro del clúster de Incus donde corre la VM (necesita virtualización: x86)"
  type        = string
  default     = "eve"
}

variable "lb_address" {
  description = "IP del balanceador en la LAN: libre dentro de 192.168.23.224/28 (ipv4.routes de la uplink de OVN)"
  type        = string
  default     = "192.168.23.226"
}
