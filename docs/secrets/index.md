# Gestión de Secretos

!!! info "Parte de la guía de implementación"
    - **[Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)** — Fase 4 wave 0; CAPN (Cluster API Provider for Incus) Fase 6.
    - **OAuth Dex** — [Fase 4 paso 4.7](../implementacion/fase-4-gitops.md#47-secretos-oauth-github-vcluster-incus-ui).
    - **Plataforma symintel** (Apps de ArgoCD, ARC y OpenTofu, FTP) — [1Password → clúster](../symintel/github.md#paso-3-cluster-y-secretos-de-plataforma).

## Diagrama — tres vías de secretos

```mermaid
flowchart LR
  subgraph git [En_git]
    SS[Sealed_Secrets]
    SOPS[SOPS_age]
  end
  subgraph station [Estacion_operador]
    OP[1Password_SDK_DesktopAuth]
  end
  subgraph cluster [En_cluster]
    SEC[k8s_Secret]
  end
  SS --> SEC
  SOPS --> git
  OP --> SEC
```

## Sealed Secrets (default en clúster)

[Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) — un controller
(~20–30 MB RAM), sin cuenta externa.

```bash
kubeseal --format yaml < secret-plano.yaml > secret-sellado.yaml
kubectl apply -f secret-sellado.yaml
rm secret-plano.yaml
```

!!! warning "La llave de cifrado vive en 1Password"
    Por defecto el controller genera su par de llaves dentro del clúster (y lo
    renueva cada 30 días): si reinstalas K3s, se pierde y los `SealedSecret`
    de git ya no se pueden descifrar. Aquí el par se genera **una vez**, se
    guarda en 1Password (item `sealed-secrets`) y
    `playbook-platform-secrets.yml` lo lleva al clúster; la renovación
    automática está desactivada (`keyrenewperiod: "0"`). Cómo generarlo:
    [Plataforma symintel — Paso 2](../symintel/github.md#paso-2-repos-app-de-argocd-y-ftp-manual).

    Como el certificado (la llave pública) también está en 1Password, puedes
    sellar sin tener acceso al clúster:
    `kubeseal --cert tls.crt --format yaml < secret-plano.yaml > secret-sellado.yaml`.

## SOPS + age (complemento, cero pods)

[SOPS](https://github.com/getsops/sops) — config pre-bootstrap (tokens Incus, etc.).

```bash
age-keygen -o key.txt
sops --encrypt --age <public-key> secrets.yaml > secrets.enc.yaml
```

## OAuth Dex (GitHub + vCluster + Incus UI) — 1Password SDK local

Credenciales de **GitHub OAuth App** y clientes Dex **vCluster Platform** e
**Incus UI (interfaz de usuario)** no van en git.

| Origen | Campos |
|---|---|
| **GitHub** (OAuth App de la org `symintel`) | `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` |
| **Ansible** (`playbook-dex-oauth-secrets.yml`) | `VCLUSTER_CLIENT_SECRET` (genera en 1Password si falta; aplica en Dex y Helm) |

`VCLUSTER_CLIENT_SECRET` **no** se crea en GitHub: Ansible lo genera en 1Password si falta.
Incus no usa secreto (es un cliente OIDC público en Dex).

Se leen con el **[1Password Python SDK](https://github.com/1Password/onepassword-sdk-python)**
y **DesktopAuth** en la estación donde la app 1Password está desbloqueada.

Por defecto: **cuenta personal** (`ONEPASSWORD_ACCOUNT_NAME=Personal`), bóveda
**`HomeLab`**, un ítem con campos `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`,
`VCLUSTER_CLIENT_SECRET`. Probar: `ansible/scripts/test-1password.py`.

Homepage `https://argocd.homelab.local` (informativa); Redirect URIs
`https://argocd.homelab.local/api/dex/callback` (crítico).

Detalle: [Fase 4 — 4.7](../implementacion/fase-4-gitops.md#47-secretos-oauth-github-vcluster-incus-ui)
· [`1password.md`](https://github.com/symintel/gitops/blob/main/argocd/secrets/1password.md)

## Monitoreo: webhooks de Discord, ping de healthchecks.io y Grafana (1Password → Secrets del clúster)

Opcional ([Fase 4 — 4.13](../implementacion/fase-4-gitops.md#413-monitoreo-y-alertas-opcional)). Cómo crear las credenciales:
[Discord y healthchecks.io](../symintel/discord-healthchecks.md). `playbook-platform-secrets.yml` crea,
en el namespace `monitoring`, tres Secrets desde 1Password; sus valores nunca pasan por git porque el repo es público.

| Item de 1Password | Campos | Secret en el clúster |
|---|---|---|
| `discord-webhooks` | `critical`, `warnings` | `monitoring/discord-webhooks` |
| `healthchecks-ping` | `url` | `monitoring/healthchecks-ping` |
| `grafana-admin` | `password` (y `username`, opcional) | `monitoring/grafana-admin` |

Alertmanager lee las URL como archivos montados (`webhook_url_file`), así que ni siquiera aparecen en su configuración. El script
exige que las dos URL de Discord tengan el formato `https://discord.com/api/webhooks/<id>/<token>`. Para rotar un webhook, bórralo y
créalo de nuevo en Discord, actualiza el item y vuelve a correr el playbook.

## Rotación de password de root (1Password SDK local)

[`playbook-rotate-root-passwords.yml`](https://github.com/symintel/homelab/blob/main/ansible/playbook-rotate-root-passwords.yml)
genera una password nueva por nodo (no idempotente a propósito — cada
corrida rota), la aplica en el `root` local de cada host (`become` +
`ansible.builtin.user`, hasheada con `password_hash('sha512')`) y la guarda
en la bóveda **`HomeLab`**, un ítem por host (`root@invincible`,
`root@oliver`, `root@deborah`, campo `password`). No toca SSH (Secure Shell) — el login de
`root` por SSH ya está deshabilitado por `host_hardening`
(`PermitRootLogin no`); esto es defensa en profundidad para consola/`su -`.

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml \
  --limit deborah
```

<div class="card">
  <div class="card-kicker">Análisis de trade-offs</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Sealed Secrets</div>
      <div class="text-muted">Cifrado en git; controller ligero (~30 MB)</div>
      <div class="text-muted">Solo en clúster; no sirve pre-bootstrap</div>
    </div>
    <div class="card-col">
      <div class="card-title">SOPS + age</div>
      <div class="text-muted">Cero pods; archivos cifrados en repo</div>
      <div class="text-muted">Clave age en la estación; flujo manual</div>
    </div>
    <div class="card-col">
      <div class="card-title">1Password SDK</div>
      <div class="text-muted">OAuth fuera de git; DesktopAuth</div>
      <div class="text-muted">App desbloqueada; no para SealedSecret en CAPN</div>
    </div>
    <div class="card-col">
      <div class="card-title">Vault / ESO <span class="tag tag-neutral">descartado</span></div>
      <div class="text-muted">Enterprise-grade</div>
      <div class="text-muted">RAM y complejidad excesivas en HomeLab</div>
    </div>
  </div>
</div>

## Descartados

- **HashiCorp Vault** — demasiado pesado para el M700.
- **1Password + ESO (External Secrets Operator) en clúster** — requiere plan Business; usamos **SDK (Software Development Kit) Python local** (DesktopAuth) desde la estación.
- **RustyVault** — proyecto joven, sin ARM64 (arquitectura ARM de 64 bits) confirmado.

Stack completo: **[Stack tecnológico](../implementacion/stack-tecnologico.md)**.
