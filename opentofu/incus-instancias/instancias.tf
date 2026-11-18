# Contenedor de aplicación (imagen OCI de Docker Hub): un nginx en la red OVN.
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

  # El balanceador necesita su IP: se espera a que la tenga.
  wait_for {
    type = "ipv4"
  }
}

# Máquina virtual Debian 13 pequeña, en la misma red.
resource "incus_instance" "vm" {
  name   = "${var.prefix}-vm"
  image  = "images:debian/13"
  type   = "virtual-machine"
  target = var.vm_target

  config = {
    "limits.cpu"    = "1"
    "limits.memory" = "1GiB"
  }

  device {
    name = "eth0"
    type = "nic"
    properties = {
      network = var.network
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
