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
