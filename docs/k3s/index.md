# K3s — Instalación manual (referencia)

!!! info "Camino recomendado"
    Usa **[Fase 3 — K3s](../implementacion/fase-3-k3s.md)** con
    `playbook-k3s.yml`. Esta página documenta pasos **manuales** (curl) como
    alternativa legacy.

Clúster K3s (distribución ligera de Kubernetes) híbrido sobre los 3 nodos del HomeLab.

> Los hostnames del HomeLab siguen la serie *Invincible* — ver
> [personajes](https://invincible.fandom.com/es/wiki/Categor%C3%ADa:Personajes).

## Estado actual del clúster

| Nodo | IP | Rol K3s | Pods destacados (discovery) |
|---|---|---|---|
| deborah | 192.168.20.5 | server (control-plane) | API `:6443` |
| invincible | 192.168.20.6 | agent (worker) | ArgoCD application-controller, svclb-traefik |
| oliver | 192.168.20.7 | agent (worker) | CoreDNS, metrics-server, local-path-provisioner |

Verificación desde un nodo con acceso al API (Application Programming Interface) server:

```bash
kubectl get nodes -o wide
kubectl get pods -A
```

!!! warning "Traefik residual"
    El cluster se instaló con `--disable traefik`, pero persisten pods
    `svclb-traefik-*` (ServiceLB de K3s). Eliminarlos con el rol
    `k3s_cleanup_traefik` o `ansible-playbook playbook-k3s.yml --tags traefik`.

!!! warning "Control-plane tras reboot"
    Si `deborah` no expone `:6443` tras reinicio, verificar:
    `sudo systemctl enable --now k3s && sudo journalctl -u k3s -n 50`

## 1. Prerrequisitos (los 3 nodos)

```bash
# Deshabilitar swap (requerido por K3s)
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Módulos de red y sysctl para el CNI (Flannel/VXLAN por defecto)
cat <<EOF | sudo tee /etc/modules-load.d/k3s.conf
br_netfilter
overlay
EOF
sudo modprobe br_netfilter overlay

cat <<EOF | sudo tee /etc/sysctl.d/k3s.conf
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
```

Desactiva swap (K3s lo exige para que el scheduler sea predecible), carga
los módulos de kernel que necesita el CNI (Container Network Interface) para enrutar tráfico entre pods,
y habilita el forwarding IP para que cada nodo pueda actuar como router de
pods.

!!! note "Red"
    Si estos nodos corren instancias dentro del clúster Incus (ver
    [Clúster Incus](../incus/cluster-setup.md)), usa el mismo bridge/cluster
    group ya definido — no hace falta un puente adicional solo para K3s.

Automatizable con: `ansible-playbook -i inventory.ini playbook-k3s.yml --tags prereqs`

Opciones bootstrap (kube-vip, ArgoCD controller, labels, …):
[`playbook-options.md`](playbook-options.md). GitOps:
[`Fase 4 — GitOps`](../implementacion/fase-4-gitops.md).

## 2. Instalación del control-plane (deborah)

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.36.5+k3s1 \
  INSTALL_K3S_EXEC="server \
  --disable traefik \
  --disable servicelb \
  --write-kubeconfig-mode 600 \
  --node-ip 192.168.20.5 \
  --tls-san 192.168.20.5 \
  --tls-san deborah" sh -
```

- `--disable traefik/servicelb`: se instalan controladamente más adelante
  (o se sustituyen por un controlador de Gateway API + MetalLB) para no perder control
  sobre versiones.
- `--write-kubeconfig-mode 600`: kubeconfig legible solo por root (endurecido
  vs 644).
- `--tls-san`: agrega la IP fija al certificado del API server, evitando
  errores TLS (Transport Layer Security) si se accede por IP en vez de hostname.

Token para unir workers:

```bash
sudo cat /var/lib/rancher/k3s/server/node-token
```

Automatizable con: `ansible-playbook -i inventory.ini playbook-k3s.yml --limit k3s_server`

## 3. Unión de workers

**invincible (15.5 GB — también corre CAPN como management cluster):**

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.36.5+k3s1 \
  K3S_URL=https://192.168.20.5:6443 \
  K3S_TOKEN=<TOKEN> \
  INSTALL_K3S_EXEC="agent --node-ip 192.168.20.6" sh -
```

**oliver (7.7 GB — perfil ligero, mismo criterio que su `scheduler.instance
manual` en Incus):**

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.36.5+k3s1 \
  K3S_URL=https://192.168.20.5:6443 \
  K3S_TOKEN=<TOKEN> \
  INSTALL_K3S_EXEC="agent --node-ip 192.168.20.7 --kubelet-arg=max-pods=110" sh -
```

Automatizable con: `ansible-playbook -i inventory.ini playbook-k3s.yml --limit k3s_agent`

## 4. Verificación

```bash
kubectl get nodes -o wide
kubectl get pods -A
```

Etiqueta los nodos por arquitectura y capacidad para poder usar
`nodeSelector`/`nodeAffinity` en los manifiestos:

```bash
kubectl label node oliver workload-tier=light
kubectl label node deborah workload-tier=heavy kubernetes.io/arch=arm64
kubectl label node invincible node.longhorn.io/create-default-disk=true
kubectl label node deborah node.longhorn.io/create-default-disk=true
kubectl label node oliver node.longhorn.io/create-default-disk=false
```

!!! warning "Multi-arch"
    Cualquier imagen de contenedor debe soportar `arm64/v8`
    (`docker manifest inspect <imagen>`) antes de programarla sin
    `nodeSelector`, o fallará en `deborah`.

## 5. Almacenamiento

Ver [Storage](../storage/index.md) para el detalle de OpenEBS/Longhorn
replicado x86↔arm64. Manifiestos GitOps en [`gitops/storage/`](https://github.com/maceosoft/gitops/tree/main/storage).

## 6. Plan de actualización automática

Manifiestos versionados en [`gitops/k3s-upgrade/`](https://github.com/maceosoft/gitops/tree/main/k3s-upgrade).

### 6.1 K3s (server + agents) — `system-upgrade-controller`

```bash
kubectl apply -f https://github.com/rancher/system-upgrade-controller/releases/latest/download/system-upgrade-controller.yaml
kubectl apply -f https://github.com/rancher/system-upgrade-controller/releases/latest/download/crd.yaml
kubectl apply -f gitops/k3s-upgrade/
```

`concurrency: 1` es intencional en un clúster de 3 nodos: nunca deja el
clúster sin capacidad de failover completa. El controlador revisa el
canal `stable` periódicamente y, al detectar versión nueva, cordona y
drena un nodo a la vez — `deborah` (control-plane) primero, luego
`invincible`/`oliver`.

### 6.2 Sistema operativo base (los 3 nodos)

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

En `/etc/apt/apt.conf.d/50unattended-upgrades`, solo parches de seguridad
y reinicio automático **escalonado** por nodo para que nunca los tres se
reinicien a la vez:

```
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:30";
```

| Nodo | Hora de reinicio sugerida |
|---|---|
| deborah | 04:00 (control-plane primero, ventana de mantenimiento más corta) |
| invincible | 04:20 |
| oliver | 04:40 |

### 6.3 Incus

Sigue el ciclo de paquetes del repo Zabbly:

```bash
sudo apt update && sudo apt upgrade -y incus incus-client
```

Si el clustering de Incus está activo, verificar que las 3 versiones
mayores coincidan antes de actualizar — un desfase de versión mayor entre
miembros del clúster Incus puede romper el quorum.

### 6.4 Resumen de cadencia

| Componente | Mecanismo | Frecuencia | Ventana |
|---|---|---|---|
| K3s (server/agents) | system-upgrade-controller, canal stable | Automático al detectar release | Continuo, 1 nodo a la vez, control-plane primero |
| SO base | unattended-upgrades | Diario (solo seguridad) | 04:00–04:40, escalonado por nodo |
| Incus | apt manual o cron mensual | Mensual | Mantenimiento programado |

## 7. Checklist post-instalación

- [x] K3s v1.36.5+k3s1 instalado (canal stable)
- [x] Workers invincible/oliver unidos al API en `192.168.20.5:6443`
- [x] Módulos overlay/br_netfilter cargados en workers
- [x] ArgoCD desplegado (application-controller en invincible)
- [ ] `kubectl get nodes` muestra 3 nodos en `Ready` (verificar CP tras reboot)
- [ ] Etiquetas de arquitectura, tier y Longhorn aplicadas
- [ ] Traefik svclb eliminado
- [ ] `system-upgrade-controller` desplegado con ambos `Plan` aplicados
- [ ] `unattended-upgrades` activo con horarios escalonados por nodo
- [ ] kubeconfig respaldado fuera del clúster (nunca commiteado — ver `.gitignore`)
