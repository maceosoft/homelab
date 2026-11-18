# Máquina virtual Debian 13 (variante cloud): cloud-init instala nginx y genera una página con datos de la VM.
resource "incus_instance" "vm" {
  name   = "${var.prefix}-vm"
  image  = "images:debian/13/cloud"
  type   = "virtual-machine"
  target = var.vm_target

  config = {
    "limits.cpu"                = "1"
    "limits.memory"             = "1GiB"
    "cloud-init.user-data"      = templatefile("${path.module}/plantillas/vm-cloud-init.yaml", { prefix = var.prefix })
    "cloud-init.network-config" = file("${path.module}/plantillas/vm-network-config.yaml")
  }

  device {
    name = "eth0"
    type = "nic"
    properties = {
      network = var.network
    }
  }

  # El contenedor necesita la IP de la VM, y los comandos de exec, su agente.
  wait_for {
    type = "agent"
  }

  wait_for {
    type = "ipv4"
  }

  # Sin esto, el apply termina antes de que cloud-init instale nginx y /vm/ responde 502 un par de minutos.
  exec = {
    "esperar-cloud-init" = {
      command = ["cloud-init", "status", "--wait"]
      timeout = "10m"
    }
  }
}

# Contenedor de aplicación (imagen OCI de Docker Hub): nginx con su página en / y la VM en /vm/.
resource "incus_instance" "web" {
  name   = "${var.prefix}-web"
  image  = "docker:nginx:1.29-alpine"
  type   = "container"
  target = var.web_target

  device {
    name = "eth0"
    type = "nic"
    properties = {
      network = var.network
    }
  }

  file {
    target_path = "/usr/share/nginx/html/index.html"
    content     = templatefile("${path.module}/plantillas/web-index.html", { prefix = var.prefix, vm_ip = incus_instance.vm.ipv4_address })
    mode        = "0644"
  }

  file {
    target_path = "/etc/nginx/conf.d/default.conf"
    content     = templatefile("${path.module}/plantillas/web-nginx.conf", { vm_ip = incus_instance.vm.ipv4_address })
    mode        = "0644"
  }

  # El balanceador necesita su IP: se espera a que la tenga.
  wait_for {
    type = "ipv4"
  }

  # nginx arranca antes de que OpenTofu copie los archivos: sin recargar, sigue con su default.conf original y
  # /vm/ responde 404.
  exec = {
    "recargar-nginx" = {
      command = ["nginx", "-s", "reload"]
    }
  }
}

# Balanceador de OVN: publica el puerto 80 del contenedor en una IP de la LAN.
resource "incus_network_lb" "web" {
  network        = var.network
  listen_address = var.lb_address
  description    = "nginx de ${var.prefix} (OpenTofu, opentofu/incus-instancias)"

  backend {
    name           = "web"
    target_address = incus_instance.web.ipv4_address
    target_port    = "80"
  }

  port {
    listen_port    = "80"
    target_backend = ["web"]
  }
}
