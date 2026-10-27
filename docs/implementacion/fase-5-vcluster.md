# Fase 5 — vCluster Platform (opcional)

## Objetivo

UI (interfaz de usuario) web para **clústeres virtuales** y el **management K3s (distribución ligera de Kubernetes)** (connected cluster),
con SSO (inicio de sesión único) vía Dex/GitHub y descarga de kubeconfig desde el navegador.

## Qué aprendes

Un **vCluster** expone una API (Application Programming Interface) Kubernetes aislada sin levantar VMs (máquinas virtuales) Incus;
[vCluster Platform](https://www.vcluster.com/docs/platform/) añade UI, SSO y
kubeconfig desde el navegador.

!!! abstract "Aprende esta fase"
    **En simple:** un vCluster es un departamento dentro del departamento: un Kubernetes virtual,
    aislado, que vive dentro de otro. Cada equipo recibe "su propio clúster" sin pagar el costo de
    montar uno nuevo.

    **Conceptos clave**

    - **Clúster virtual:** una API de Kubernetes aislada que corre como pods en el clúster anfitrión.
    - **Multi-tenancy (varios inquilinos):** compartir una misma infraestructura entre equipos sin que se vean entre sí.
    - **Kubeconfig:** el archivo que da acceso a un clúster; la plataforma permite descargarlo desde el navegador.
    - **SSO (inicio de sesión único) y OIDC (OpenID Connect):** iniciar sesión con GitHub a través de Dex, sin otra contraseña.

    **Reto práctico (solo lectura):** lee el flujo de inicio de sesión de la Fase 4 y explica con tus propias palabras,
    en cuatro pasos, qué pasa cuando alguien entra con GitHub.

    ??? question "¿Qué ventaja tiene un vCluster frente a una máquina virtual completa?"
        Arranca en segundos y gasta menos recursos, porque comparte el kernel y la infraestructura del anfitrión.

    ??? question "¿Qué papel cumple Dex en el login?"
        Es el intermediario: recibe el inicio de sesión de GitHub y se lo traduce a las aplicaciones (Argo CD, Platform, Incus).

    ¿Dudas? Usa el botón **Aprende con IA** junto a cada título, o la página [Aprende](../aprende.md).

## Stack de esta fase

```mermaid
flowchart TB
  User[Usuario] --> VP[vcluster_homelab_local]
  VP --> Dex[Dex_ArgoCD]
  Dex --> GH[GitHub]
  VP --> VC[vCluster_API]
  VC --> Mgmt[Pods_en_K3s_management]
```

- **[vCluster Platform](https://www.vcluster.com/docs/platform/)** — UI + control plane virtual; Fase 5.
- **[Dex](https://dexidp.io/docs/)** — IdP (proveedor de identidad) OIDC; configurado en Fase 4.
- **[Gateway API](https://gateway-api.sigs.k8s.io/)** — Expone Platform en LAN (red local) con un `HTTPRoute` sobre el Gateway `homelab`.

Profundización: [vCluster Platform](../vcluster/index.md)

**Esta decisión en otros entornos**

=== "🏠 En casa"

    vCluster Platform corre dentro del mismo K3s de management: creas clústeres virtuales para probar cosas sin
    levantar VMs nuevas ni gastar la poca RAM que hay. Es opcional y su Sync es manual.

=== "🏢 En la empresa"

    - **Beneficios:** cada equipo o cliente recibe su propio clúster (su API, sus CRD, sus permisos de admin) sin que
      la empresa mantenga un clúster real por cada uno; los entornos efímeros de cada PR se crean en segundos y se
      borran al cerrarlo, y el acceso queda centralizado en el SSO corporativo.
    - **Aislamiento:** los vClusters comparten nodos y kernel con el clúster anfitrión. Para clientes que no se
      confían entre sí se suman cuotas, NetworkPolicies y nodos dedicados, o se mantienen clústeres separados.
    - **Soporte comercial:** vCluster es open source y vCluster Platform tiene un
      [plan Enterprise](https://www.vcluster.com/pricing) con soporte, SLA y funciones de seguridad y cumplimiento.
    - **Permisos:** en vez de asignar Cluster Access a mano, se mapean los grupos del IdP corporativo a proyectos
      y roles, y se revisan en las auditorías de acceso.
    - **Cuándo conviene lo mismo que el HomeLab:** plataformas internas con muchos equipos pequeños, entornos de
      prueba por PR y laboratorios de formación, donde un clúster real por equipo costaría demasiado.

=== "☁️ En la nube"

    | Nube | Servicio equivalente |
    |---|---|
    | GCP | [GKE](https://cloud.google.com/kubernetes-engine) con [equipos de flota](https://cloud.google.com/kubernetes-engine/fleet-management/docs/team-management) |
    | AWS | [Amazon EKS](https://aws.amazon.com/eks/) ([aislamiento de inquilinos](https://docs.aws.amazon.com/eks/latest/best-practices/tenant-isolation.html)) |
    | Azure | [AKS](https://azure.microsoft.com/en-us/products/kubernetes-service) ([aislamiento de clústeres](https://learn.microsoft.com/en-us/azure/aks/operator-best-practices-cluster-isolation)) |
    | Oracle Cloud (OCI) | [OCI Kubernetes Engine (OKE)](https://www.oracle.com/cloud/cloud-native/kubernetes-engine/) |

    En la nube la opción simple es un clúster administrado por equipo: aislamiento fuerte y SLA, pero pagas cada
    control plane y multiplicas lo que hay que actualizar. vCluster corre igual sobre cualquiera de ellos y reduce
    el número de clústeres reales, a cambio de un aislamiento más débil y otra pieza que operar.

## Antes de empezar

- [ ] [Fase 4 — GitOps](fase-4-gitops.md) completada (Gateway, Dex y los secretos OAuth —Open Authorization— en 1Password).
- [ ] `vcluster.homelab.local` resuelve (DNS de la [sección 4.8](fase-4-gitops.md#48-dns-de-homelablocal) o, si no, `/etc/hosts`).

## Ejecutar

```bash
kubectl apply -f gitops/argocd/apps/vcluster-platform.yaml
```

=== "🖱️ Desde la interfaz"

    Argo CD UI → Application `vcluster-platform` → **Sync**.

=== "⌨️ Desde la consola"

    Con la CLI de Argo CD:

    ```bash
    argocd login argocd.homelab.local --grpc-web
    argocd app sync vcluster-platform
    ```

Secretos OAuth (si no en 4.7): [`argocd/secrets/1password.md`](https://github.com/maceosoft/gitops/blob/main/argocd/secrets/1password.md).

Tras sync de `vcluster-platform`, aplica `VCLUSTER_CLIENT_SECRET` en Helm:

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-dex-oauth-secrets.yml \
  --tags vcluster -e dex_oauth.apply_vcluster=true
```

## Opciones

| Decisión | Default HomeLab |
|---|---|
| Sync Argo CD | Manual (comentada en `homelab-root`) |
| Login admin | `auth.password.disabled: false` hasta validar SSO GitHub |
| Permisos usuarios SSO | **Denegar por defecto** — sin Cluster Access / proyecto asignado no ven clústeres ni kubeconfig |

<div class="card">
  <div class="card-kicker">Análisis de trade-offs</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Sync manual</div>
      <div class="text-muted">Evita borrado accidental de Platform</div>
      <div class="text-muted">Paso extra en Argo CD</div>
    </div>
    <div class="card-col">
      <div class="card-title">Admin password habilitado</div>
      <div class="text-muted">Acceso de rescate sin GitHub</div>
      <div class="text-muted">Superficie de ataque si no se deshabilita tras SSO</div>
    </div>
    <div class="card-col">
      <div class="card-title">Solo SSO GitHub</div>
      <div class="text-muted">Un solo IdP; alineado con Dex</div>
      <div class="text-muted">Sin login si Dex/GitHub caen</div>
    </div>
    <div class="card-col">
      <div class="card-title">Kubeconfig web (Platform)</div>
      <div class="text-muted">Sin <code>scp</code>; permisos centralizados</div>
      <div class="text-muted">Requiere asignar Cluster Access explícitamente</div>
    </div>
    <div class="card-col">
      <div class="card-title">CLI (<code>vcluster connect</code>)</div>
      <div class="text-muted">Automatizable en scripts</div>
      <div class="text-muted">Sin SSO integrado en el flujo</div>
    </div>
  </div>
</div>

## Permisos: denegar por defecto

[vCluster Platform](https://www.vcluster.com/docs/platform/administer/users-permissions/overview)
no concede acceso a clústeres conectados ni vClusters solo por iniciar sesión.
Un usuario SSO nuevo **no ve recursos** hasta que un admin le asigne:

- **Cluster Access** — kubeconfig del management K3s (connected cluster)
- **Proyecto + rol** — crear/gestionar vClusters dentro de un proyecto
- **Management Role** — operaciones de plataforma (solo admins)

Pasos típicos para el primer operador (como admin de Platform):

1. **Clusters** → **Cluster Access** → Create → usuario/equipo + ClusterRole
2. Para vClusters: asignar al usuario a un **Project** con rol adecuado
3. Los equipos de GitHub llegan como grupos `loft-*` (OIDC)

## Verificar

```bash
kubectl get pods -n vcluster-platform
curl -kI https://vcluster.homelab.local
```

1. Abre [`https://vcluster.homelab.local`](https://vcluster.homelab.local)
2. Login with SSO (GitHub)
3. New Virtual Cluster → Download kubeconfig

## Kubeconfig del management K3s

[vCluster Platform](https://www.vcluster.com/docs/platform/) registra
automáticamente el clúster **host** (el K3s donde corre Platform) como
**connected cluster**. Desde la misma UI obtienes el kubeconfig del management
cluster, no solo el de vClusters.

1. Login SSO en [`https://vcluster.homelab.local`](https://vcluster.homelab.local)
2. **Clusters** → selecciona el clúster host (p. ej. el nombre del contexto K3s)
3. **Connect** / **Download kubeconfig**
4. `export KUBECONFIG=~/Downloads/kubeconfig.yaml && kubectl get nodes`

Si no ves el clúster o no puedes descargar kubeconfig, asigna **Cluster Access**
al usuario o equipo en Platform. Sin esa asignación, el login SSO funciona pero
**no hay clústeres ni kubeconfig visibles** (denegar por defecto). Los grupos
OIDC de GitHub llegan con prefijo `loft-` (ver
[`platform.yaml`](https://github.com/maceosoft/gitops/blob/main/vcluster/values/platform.yaml)).

## Accesos web del HomeLab

| Recurso | URL | Qué obtienes |
|---|---|---|
| Management K3s | [`https://vcluster.homelab.local`](https://vcluster.homelab.local) | Kubeconfig del host K3s (connected cluster) |
| vClusters | [`https://vcluster.homelab.local`](https://vcluster.homelab.local) | Kubeconfig de cada clúster virtual |
| Incus cluster | [`https://incus.homelab.local:8443`](https://incus.homelab.local:8443) | UI de administración Incus (OIDC tras Fase 4) |

Alternativa CLI (interfaz de línea de comandos) para el management K3s: [`fase-4-gitops.md` 4.1](fase-4-gitops.md#41-acceso-kubectl) (`ssh … sudo cat` o Ansible).

## Si falla

| Síntoma | Revisar |
|---|---|
| El SSO vuelve al login una y otra vez | Secretos Dex + `playbook-dex-oauth-secrets.yml --tags vcluster` |
| PVC pending | OpenEBS/Longhorn Healthy |

## Siguiente

Opcional: **[→ Fase 6 — CAPN (Cluster API Provider for Incus)](fase-6-capn.md)** ·
**[Resumen del HomeLab](resumen-homelab.md)**
