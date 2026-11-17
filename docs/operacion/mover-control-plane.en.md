# Move K3s control plane to another node (deborah → oliver)

Procedure to move the **control plane** (the K3s server that holds cluster state and serves the API) from `deborah` to `oliver`, leaving `deborah` as a **worker**. Performed during a **maintenance window** with a person at the keyboard: the playbook pauses at several **pause points** for you to confirm each stage.

!!! note "Not planned"
    The control plane stays on `deborah`. This procedure is documented in case it ever needs to be moved to another node.

## Why it might be moved

`deborah` is the machine with the most memory (31 GB), but it also runs Ollama, serves as the LAN DNS, and has a slow eMMC (soldered flash memory). A loaded model competes with the control plane for memory. `oliver` is a lightweight node (label `workload-tier=light`) with a steady load, and `deborah` is freed up for models and heavy workloads.

!!! danger "Cluster is not rebuilt"
    Longhorn (storage) stores its metadata inside cluster state: if lost, volumes become orphaned. That is why this procedure **transfers existing state**; it does not reinstall from scratch. Do not start without a verified backup.

## How the move works

Today K3s runs with a single server and SQLite (a single file). The official K3s docs do not describe how to move that file to another node (and the token includes the CA hash, the cluster's certificate authority). What *is* documented is converting the datastore to **embedded etcd** (Kubernetes' distributed database, integrated into K3s), joining another server with the same token, and ending up with a single server. The playbook
[`playbook-k3s-move-controlplane.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-k3s-move-controlplane.yml)
does exactly that, in stages, each with its tag (`tag`):

| Stage | Tag | What it does | API |
|---|---|---|---|
| 1 | `preflight` | Checks: nodes `Ready`, Longhorn without degraded volumes, Argo CD synced | up |
| 2 | `backup` | **Encrypted** backup of state, stored off-node (stops K3s for a few minutes on source) and generation of a distinct *agent-token* from the server token | down briefly |
| 3 | `convert` | Converts `deborah` to etcd (`--cluster-init`) with security flags and repoints agents to name `k3s.homelab.local` | down briefly |
| 4 | `join` | Drains `oliver`, removes its agent and joins it as second server | up |
| 5 | `dns` | `k3s.homelab.local` switches to point at `oliver` | up |
| 6 | `retire` | Leaves `oliver` as sole etcd member and `deborah` as agent | down briefly |
| 7 | `verify` | Final verification, summary of manual steps and secure deletion (`shred`) of plaintext backup and `/root/k3s-move-*` on nodes | up |

Rollback (`--tags rollback`) **never runs unattended**.

!!! warning "Two etcd members during the window"
    Between stages 4 and 6 the cluster has two etcd members (`deborah` and `oliver`). With two members there is no fault tolerance: if one goes down, the other loses quorum and the API stops responding. Do not touch the nodes outside the playbook during that interval.

## Prerequisites

- [ ] A window where the API can be unresponsive for several minutes in stages 2, 3 and 6: Argo CD does not sync and `kubectl` does not respond; running workloads keep running, except `deborah` pods, which are drained in stage 6.
- [ ] SSH access to `deborah` and `oliver` ([SSH Access](acceso-ssh.md)) and physical access to `deborah`.
- [ ] Healthy Longhorn and synced Argo CD (the `preflight` checks this; Argo CD check can be skipped with `k3s_move_allow_unsynced`, but not recommended).
- [ ] `playbook-bind-dns.yml` already applied, with the `k3s` record in the `homelab.local` zone: variable `k3s_api_endpoint` (`k3s.homelab.local`) replaces the control plane's fixed IP in agents, kubeconfig and API cert SANs (Subject Alternative Names).
- [ ] HomeLab CA on nodes (role `opkssh`), because new servers trust Dex for user login.
- [ ] An encryption method for the backup (contains cluster token and certificates): an `age` public key (`k3s_move_backup_age_recipient`) or a password for `gpg` (`k3s_move_backup_passphrase`, preferably via environment variable). Without either the playbook aborts, unless forced with `-e k3s_move_backup_unencrypted=true` (not recommended).
- [ ] `oliver` with ~5 GB free memory. If it has heavy workloads, move them first.

## Step by step

From `ansible/`:

1. **Dry run, no changes:**

    ```bash
    ansible-playbook -i inventory.ini playbook-k3s-move-controlplane.yml --check --diff
    ```

2. **Actual run.** With pauses enabled (default), the playbook asks for confirmation before backup, before converting to etcd, before joining `oliver`, before repointing DNS, and before removing the source:

    ```bash
    ansible-playbook -i inventory.ini playbook-k3s-move-controlplane.yml
    ```

    Useful variables: `k3s_move_target` (destination, default `oliver`), `k3s_move_backup_dir` (where backup is stored, default `~/k3s-move-backups` on your machine), `k3s_move_backup_age_recipient` or `k3s_move_backup_passphrase` (encryption), `k3s_move_agent_token` (if you want to pin the *agent-token* instead of generating it), `k3s_move_drain_source`, `k3s_move_rotate_secrets`, `k3s_move_allow_unsynced` and `k3s_move_confirm=false` for non-interactive (not recommended).

3. **Pause points.**
    - After backup: open the file and verify its checksum before continuing.
    - Before converting: this is the step that **cannot be undone without rollback**.
    - After joining `oliver`: `kubectl get nodes` should show two servers.
    - After repointing DNS: `dig +short k3s.homelab.local @192.168.20.5` should return the IP of `oliver`.

!!! tip "If something doesn't look right, stop"
    Each pause allows aborting with `Ctrl+C`. If the playbook is interrupted after stage 3, do not resume with loose `--tags`: stages 4 and 6 need the token obtained in stage 3, within the same run.

When finished, the playbook **does not modify the inventory**: you do that, as explained below. Agents stop using the server token and switch to their own **agent-token**, which ends up in `<k3s_move_backup_dir>/agent-token`.

With the migration, the new server's hardening also applies: flags `oidc-*` toward Dex (human login, with `--oidc-username-prefix=oidc:` and `--oidc-groups-prefix=oidc:`), `--secrets-encryption` (encryption of Secrets at rest), and the K3s installer verified by checksum instead of `curl | sh`. The admin certificate remains for emergencies only. See [Authentication model](../security/modelo-de-autenticacion.md).

## Verification

| What | How |
|---|---|
| Nodes | `kubectl get nodes -o wide`: `oliver` with role `control-plane`, and all in `Ready` |
| Argo CD | `kubectl -n argocd get applications`: all `Synced` and `Healthy` |
| Longhorn | UI or `kubectl -n longhorn-system get volumes.longhorn.io`: no degraded volumes |
| Kong | `curl -kI https://argocd.homelab.local` responds |
| DNS | `dig +short k3s.homelab.local @192.168.20.5` returns the IP of `oliver` |
| Pods | `kubectl get pods -A` no stuck pods (`Pending`, `CrashLoopBackOff`); those that lived on `deborah` get rescheduled |

## What changes in the inventory afterwards

The playbook does not touch these files; edit them manually when done (and commit yourself):

- [`inventory.ini`](https://github.com/maceosoft/homelab/blob/main/ansible/inventory.ini): `deborah` changes from `[k3s_server]` to `[k3s_agent]` and `oliver` changes from `[k3s_agent]` to `[k3s_server]` (and its `k3s_role`).
- `group_vars/all.yml`: `k3s_api_ip` becomes `192.168.20.7` (the IP of `oliver`) and `k3s_move_done` to `true`.
- `host_vars/deborah.yml` and `host_vars/oliver.yml`: labels and K3s options follow `k3s_move_done`; `deborah` retains `workload-tier=heavy` and `oliver` remains `light`.
- Reapply `playbook-bind-dns.yml` so the zone aligns with `k3s_api_ip`.
- **SUC plans** (*System Upgrade Controller*, the automatic K3s updater; [`addons/cluster/k3s-upgrade/`](https://github.com/maceosoft/gitops/tree/main/addons/cluster/k3s-upgrade)): they select the control plane by the label `node-role.kubernetes.io/control-plane`, so they don't change and now update `oliver` first.

Other guides discussing the control plane: [Remove or replace a node](sacar-nodo.md), [Add a node](agregar-nodo.md), [Update K3s](actualizar-k3s.md), and [Phase 3](../implementacion/fase-3-k3s.md).

## Rollback

Restore the original SQLite in `deborah` from backup and return `oliver` to agent:

```bash
  # o -e k3s_move_backup_passphrase=...
ansible-playbook -i inventory.ini playbook-k3s-move-controlplane.yml --tags rollback \
  -e k3s_move_backup_stamp=<AAAAMMDDTHHMMSS> \
  -e k3s_move_backup_age_identity=<archivo de identidad age>
```

The tag is the date part of the backup filename in the backup directory. Rollback is four steps, in this order: **1)** DNS points back to `deborah` and wait ~300 seconds for propagation (otherwise the agent reinstalled on `oliver` would try to join itself via `k3s.homelab.local`); **2)** the source is restored; **3)** `oliver` returns to agent; **4)** the other agents recover the original token. **All cluster changes after the backup are lost**: decide calmly before reverting. If you already edited the inventory, set it back as it was.

## Manual steps when finished

1. **Kubeconfig.** Regenerate yours, which pointed to the old IP:

    ```bash
    ansible-playbook -i inventory.ini playbook-k3s.yml --tags kubeconfig
    ```

2. **Save the migration secrets in 1Password.** The *agent-token* (`<k3s_move_backup_dir>/agent-token`) and the key or password used to encrypt the backup. The plaintext backup and the nodes' `/root/k3s-move-*` files are deleted automatically at the end (`shred`); only the encrypted backup on your machine remains, which is what serves for rollback.
3. **Check Argo CD, Longhorn, and Kong** with the [Verification](#verificacion) table.
4. **Dex login permissions.** The repo `gitops` includes the ClusterRoleBinding [`oidc-devops-view`](https://github.com/maceosoft/gitops/blob/main/addons/security/rbac/oidc-devops.yaml) (Application `security-rbac`, already active), which grants the ClusterRole `view` (read-only) to the group `oidc:maceosoft:devops`. It's harmless until OIDC tokens exist.

    !!! info "Why read-only and not `cluster-admin`"
        Logging in via Dex should not grant full cluster control by default: state changes go through Git and Argo CD, and the admin certificate remains for emergencies. If a person needs write access in a namespace, extend with a `RoleBinding` that binds the ClusterRole `edit` to the same group **only in that namespace**, instead of expanding the ClusterRoleBinding.

5. **Optional, Calico risk.** Verify that a regular service account cannot create global policies (see [Optional checks](../security/modelo-de-autenticacion.md#optional-checks)).

### Human login with Dex (kubelogin)

With the `oidc-*` flags enabled, you can access the API with your GitHub account instead of the admin certificate. Install the `kubelogin` plugin (`kubectl oidc-login`) and request a token:

```bash
kubectl oidc-login get-token \
  --oidc-issuer-url=https://argocd.homelab.local/api/dex \
  --oidc-client-id=kubernetes \
  --oidc-extra-scope=email,groups
```

The browser opens; the Dex `kubernetes` client is public (PKCE) and receives the response at `http://localhost:8000` (or, as a fallback, `18000`): those ports must be free on your machine. To use it permanently, configure a user in your kubeconfig with `exec` pointing to that command.

## Risks

- It is a **single** control plane (no HA, high availability): if `oliver` goes down, the cluster loses its API until restored. Already running workloads continue to run.
- Switching from SQLite to etcd is a data store change: that is why backup and rollback are part of the procedure, not an extra.

See also [Remove or replace a node](sacar-nodo.md), [Upgrade K3s](actualizar-k3s.md), and [Phase 3 — K3s](../implementacion/fase-3-k3s.md).
