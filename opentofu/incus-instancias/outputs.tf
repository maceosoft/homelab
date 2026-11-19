output "url" {
  description = "nginx desde la LAN, por el balanceador"
  value       = "http://${incus_network_lb.web.listen_address}"
}

output "web_ipv4" {
  description = "IP interna del contenedor en la red OVN (no se alcanza desde la LAN)"
  value       = incus_instance.web.ipv4_address
}

output "vm_ipv4" {
  description = "IP interna de la VM en la red OVN"
  value       = incus_instance.vm.ipv4_address
}

output "dns" {
  description = "Nombres que registra Incus solo (zona ovn.homelab.local, IPs internas)"
  value       = ["${incus_instance.web.name}.ovn.homelab.local", "${incus_instance.vm.name}.ovn.homelab.local"]
}
