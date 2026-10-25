# HomeLab — K3s + Incus + CAPN

<span class="tag tag-status">En construcción activa</span>

Un laboratorio para **aprender y operar infraestructura moderna** con equipos que cualquiera puede tener en casa:
tres computadores pequeños que se convierten en una «mini nube» con Kubernetes. La documentación explica cada paso,
por qué se hace y cómo comprobar que funcionó, y **te acompaña con inteligencia artificial (IA) mientras estudias**.

## ¿Qué es esto?

=== "En simple"

    Imagina un edificio pequeño con tres pisos. Cada piso es un computador. Un programa llamado **Incus** divide cada
    piso en departamentos (máquinas virtuales y contenedores). Encima trabaja un **gerente**, Kubernetes (en su versión
    ligera, K3s), que decide qué aplicación va en qué departamento y reemplaza a la que falle. Todo lo que está
    instalado está escrito en un **plano guardado en Git**; otro programa, Argo CD, compara el edificio con el plano y
    corrige cualquier diferencia. Y cada instalación se hace con listas de tareas automáticas (Ansible), así que
    se puede repetir igual las veces que quieras.

=== "En técnico"

    Clúster K3s híbrido (control plane ARM64, workers x86_64) sobre un clúster Incus de tres miembros (quórum con
    dqlite, cluster groups por arquitectura). Red de pods con Calico (VXLAN cross-subnet), `LoadBalancer` con MetalLB
    en L2 y entrada HTTPS por Gateway API (Kong) con TLS de una CA propia (cert-manager). Almacenamiento con OpenEBS
    LocalPV y Longhorn. La plataforma se despliega por GitOps: un ApplicationSet de Argo CD activa las apps por olas
    desde un repositorio privado, con secretos en 1Password y SSO con Dex y GitHub. Ansible hace el bootstrap de los nodos,
    OpenTofu gestiona los repositorios de GitHub y ARC ejecuta los pipelines en el propio clúster. Cluster API (CAPN)
    crea clústeres efímeros sobre Incus.

## El HomeLab de un vistazo

| Pieza | En simple | Qué hace técnicamente |
|---|---|---|
| Nodos | Los tres «pisos» del edificio | Lenovo M920q, M700 y Orange Pi 5 Plus (x86_64 y ARM64) |
| **Incus** | El que divide cada piso en departamentos | Gestiona contenedores y VM en un clúster de tres miembros |
| **K3s** | El gerente que reparte el trabajo | Kubernetes ligero: control plane en `deborah`, workers en los otros dos |
| **Calico** | Los pasillos entre departamentos | CNI: da red y direcciones a los pods |
| **MetalLB** | El número de teléfono fijo del edificio | Asigna IP de la LAN a los Services `LoadBalancer` |
| **Gateway (Kong)** | La puerta principal con portero | Recibe el tráfico HTTPS y lo envía a cada aplicación |
| **cert-manager** | La oficina que emite los carnets | Emite certificados TLS con una CA propia del HomeLab |
| **Longhorn y OpenEBS** | Bodegas: una rápida y otra con copia de seguridad | Almacenamiento local y replicado entre nodos |
| **Argo CD (GitOps)** | El inspector que compara el edificio con el plano | Sincroniza el clúster con lo que declara Git |
| **Dex** | El mostrador de identificación | SSO: inicia sesión con GitHub en ArgoCD, vCluster e Incus |
| **ARC** | Obreros que construyen y prueban | Runners de GitHub Actions dentro del clúster |
| **CAPN** | Una impresora 3D de clústeres | Cluster API para crear clústeres a partir de un manifiesto |

## Elige tu ruta

<div class="card">
  <div class="card-kicker">¿Por dónde empiezo?</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Estoy empezando</div>
      <div class="text-muted">Sigue las fases en orden. Cada una trae un bloque «Aprende esta fase» con analogías, un reto práctico y preguntas de repaso.</div>
      <div class="text-muted"><a href="implementacion/fase-0-preparacion/">Fase 0</a> · <a href="implementacion/fase-1-red/">Fase 1</a> · <a href="implementacion/fase-2-incus/">Fase 2</a> · <a href="implementacion/fase-3-k3s/">Fase 3</a> · <a href="glosario/">Glosario</a></div>
    </div>
    <div class="card-col">
      <div class="card-title">Ya sé Linux y Kubernetes</div>
      <div class="text-muted">Ve directo a las decisiones: el GitOps de la plataforma, la arquitectura y los análisis de trade-offs de cada fase.</div>
      <div class="text-muted"><a href="implementacion/fase-4-gitops/">Fase 4 — GitOps</a> · <a href="architecture/overview/">Arquitectura</a> · <a href="gitops/">Catálogo GitOps</a></div>
    </div>
    <div class="card-col">
      <div class="card-title">Vengo a operar</div>
      <div class="text-muted">Procedimientos de rutina: agregar un nodo, rotar credenciales, actualizar K3s y ArgoCD, cambiar el controlador de Gateway.</div>
      <div class="text-muted"><a href="operacion/">Operación</a> · <a href="storage/">Storage</a> · <a href="secrets/">Secretos</a></div>
    </div>
  </div>
</div>

## Aprende con IA, gratis

En cada paso de la guía hay un botón **Aprende con IA**: prepara una pregunta de tutor con el contexto de esa sección
y te lleva a un cuaderno de estudio que **responde solo con esta documentación**, con cuestionarios y resúmenes en
audio. Elige tu nivel, pulsa el botón y pega la pregunta en el chat.

- [**Cómo se usa y qué herramientas gratuitas hay**](aprende.md)
- [Abrir el cuaderno de NotebookLM](https://notebooklm.google/){ data-notebook-link="1" } (necesitas una cuenta de Google)
- Si usas otro asistente: [`llms-full.txt`](https://homelab.maceo.cl/llms-full.txt) trae toda la guía en texto plano.

## Hardware

| Nodo | Modelo | CPU | RAM (medida) | IP (`br0`) | Rol |
|---|---|---|---|---|---|
| `invincible` | Lenovo M920q | i7-8700T x86_64 | 15.5 GB | 192.168.20.6 | Incus leader · K3s worker |
| `oliver` | Lenovo M700 | i3-6100T x86_64 | 7.7 GB | 192.168.20.7 | Incus quorum · K3s worker |
| `deborah` | Orange Pi 5 Plus | RK3588 ARM64 | 31 GB | 192.168.20.5 | K3s control-plane · Incus arm64 |

Detalle medido y presupuesto RAM: [Inventario de hardware](hardware/inventory.md).

> Hostnames de la serie *Invincible* — ver
> [personajes](https://invincible.fandom.com/es/wiki/Categor%C3%ADa:Personajes).

## Empieza por acá

**Guía principal — implementación paso a paso:**

- **[Implementación — visión general](implementacion/index.md)** — Fases 0→6, timeline, forks.
- **[Stack tecnológico](implementacion/stack-tecnologico.md)** — diagrama por capas + productos.

Contexto y profundización:

- [Arquitectura (C4 Nivel 1–4)](architecture/overview.md) · [Componentes](architecture/nivel-3-componentes.md) · [Despliegue](architecture/nivel-4-despliegue.md)
- [Inventario de hardware](hardware/inventory.md)
- [Catálogo GitOps](gitops/index.md) · [Storage](storage/index.md) · [Secretos](secrets/index.md)
- [Lab Cinc/Chef](labs/cinc/index.md)

!!! note "Repositorio"
    El código (Ansible, OpenTofu, manifiestos de Kubernetes) vive en el mismo
    repo, fuera de `docs/`. Este sitio es la documentación humana; el repo
    completo es la fuente ejecutable.
