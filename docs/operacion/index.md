# Operación — procedimientos de rutina

La [guía de implementación](../implementacion/index.md) (Fases 0 a 6) levanta
el HomeLab **una vez**. Esta sección reúne lo que se hace **después**, cada
vez que haga falta: agregar piezas, mantenerlas y rotar credenciales.

Cada procedimiento dice cuándo usarlo, qué tiene que estar listo antes, los
pasos en orden, cómo verificar y qué revisar si algo falla.

| Procedimiento | Cuándo | Dónde se ejecuta |
|---|---|---|
| [URLs y accesos de los productos](urls-y-accesos.md) | Saber dónde está cada herramienta, cómo se entra y si responde | Navegador, `kubectl` |
| [Entrar por SSH a los servidores](acceso-ssh.md) | Entrar a `invincible`, `oliver` o `deborah` con tu cuenta de GitHub | Tu estación (`opkssh`, `ssh`) |
| [Monitoreo y alertas](monitoreo.md) | Ver temperaturas y uso de los nodos, entender un aviso de Discord, silenciar una alerta | Grafana, `kubectl` |
| [Agregar un repo](agregar-repo.md) | Cada proyecto nuevo en la org `symintel` | 1Password + PR en `infra` |
| [Agregar un nodo](agregar-nodo.md) | Sumar un equipo al clúster Incus y K3s | Ansible (`homelab`) |
| [Sacar o reemplazar un nodo](sacar-nodo.md) | Retirar un equipo o cambiarlo por otro | `kubectl`, Incus y Ansible |
| [Agregar un disco a un nodo](agregar-disco.md) | Más almacenamiento para Longhorn o Incus | Ansible (`homelab`) |
| [Backups y snapshots de Incus](backups-incus.md) | Programar respaldos o recuperar una instancia | Incus |
| [Actualizar K3s](actualizar-k3s.md) | Revisar las actualizaciones automáticas o fijar una versión | GitOps + Ansible |
| [Actualizar ArgoCD](actualizar-argocd.md) | Se actualiza solo a la última versión; primera actualización, fijar una versión, qué hacer si falla | GitOps + Ansible |
| [Cambiar el controlador de Gateway](cambiar-gateway.md) | Cambiar entre Kong, Traefik y NGINX; TLS de `*.homelab.local` | GitOps + `kubectl` |
| [Actualizar Debian en deborah (12 → 13)](actualizar-debian-deborah.md) | Pasar el control plane a Debian 13, con respaldo y compuerta de arranque | Ansible (`homelab`) |
| [Calico (CNI) con ArgoCD](actualizar-calico.md) | Cómo ArgoCD administra y actualiza la red de los pods | GitOps + `kubectl` |
| [Caché de los runners (ARC)](cache-arc.md) | Qué se cachea entre jobs, cómo verificarla, limpiarla o vaciarla | `kubectl` + GitOps |
| [Rotar credenciales](rotar-credenciales.md) | Periódicamente, o si una credencial se filtró | 1Password + playbooks |
| [Pipeline de gitops](pipeline-gitops.md) | Qué valida cada PR de `gitops`; activar el diff de ArgoCD (una vez) | GitHub Actions + 1Password |

!!! note "Desde dónde se corren los comandos"
    Salvo que el procedimiento diga otra cosa, los comandos de Ansible se
    corren desde la carpeta `ansible/` del repo `homelab`, y los de
    `kubectl` con el kubeconfig del HomeLab (`~/.kube/homelab-k3s.yaml`).
