# Move the K3s Control Plane to Another Node (deborah → oliver)

Procedure to transfer the **control plane** (the K3s server that stores the cluster state and serves the API) from `deborah` to `oliver`, and leave `deborah` as a **worker**. This is done during a **maintenance window**, with one person at the keyboard: the playbook pauses at several **checkpoint points** for you to confirm each stage.

!!! note "Not planned"
    The control plane stays on `deborah`. This procedure is documented in case it ever needs to change nodes.

## Why It Could Be Moved

`deborah` is the machine with the most memory (31 GB), but it also runs Ollama, serves as the LAN (local network) DNS, and has a slow eMMC (onboard flash memory). A loaded model competes with the control plane for memory. `oliver` is a lightweight node (label `workload-tier=light`) with a stable load, and `deborah` is freed up for models and heavy loads.

!!! danger "The cluster is not rebuilt"
    Longhorn (the storage) stores its metadata within the cluster state: if it is lost, the volumes become orphaned. That's why this procedure **transfers the existing state**; it does not reinstall from scratch. Without a verified backup, do not start.

## How the Transfer Is Done

Today, K3s runs with a single server and SQLite (a file). The official K3s documentation does not describe how to move that file to another node (and the token includes the CA hash, the cluster's certificate authority). What is documented is converting the data store to **embedded etcd** (Kubernetes' distributed database, integrated into K3s), adding another server with the same token, and ending up with a single server. The playbook
[`playbook-k3s-move-controlplane.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-k3s-move-controlplane.yml)
does exactly that, in stages, each with its label (`tag`):

| Stage | Label | What It Does | API |
|---|---|---|---|
| 1 | `preflight` | Checks: nodes `Ready`, Longhorn without degraded volumes, Argo CD synchronized | up |
| 2 | `backup` | Backup **encrypted** of the state, saved outside the node (stops K3s for a few minutes at the origin) and generates a different *agent-token* from the server token | down for a while |
| 3 | `convert` | Converts `deborah` to etcd (`--cluster-init`) with security flags and restarts agents to the name `k3s.homelab.local` | down for a while |
| 4 | `join` | Drains `oliver`, removes its agent, and joins it as a second server | up |
| 5 | `dns` | `k3s.homelab.local` points to `oliver` | up |
| 6 | `retire` | Leaves `oliver` as the sole etcd member and `deborah` as an agent | down for a while |
| 7 | `verify` | Final verification, summary of manual steps and secure deletion (`shred`) of the clear backup and `/root/k3s-move-*` on the nodes | up |

The rollback (`--tags rollback`) **never runs alone**.

!!! warning "During the window, there are two etcd members"
    Between stages 4 and 6, the cluster has two etcd members (`deborah` and `oliver`). With two members, there is no fault tolerance: if one goes down, the other loses quorum and the API stops responding. Do not touch the nodes outside the playbook during this interval.

## Prerequisites

- [ ] A window in which the API can be unresponsive for several minutes during stages 2, 3, and 6: Argo CD does not synchronize and `kubectl` does not respond; running loads continue, except for the `deborah` pods, which are drained in stage 6.
- [ ] SSH access to `deborah` and `oliver` ([SSH in](acceso-ssh.md)) and physical access to `deborah`.
- [ ] Healthy Longhorn and synchronized Argo CD (the `preflight` checks this; you can skip Argo CD with `k3s_move_allow_unsynced`, but it is not recommended).
- [ ] `playbook-bind-dns.yml` already applied, with the registry `k3s` in the zone `homelab.local`: the variable `k3s_api_endpoint` (`k3s.homelab.local`) replaces the fixed IP of the control plane in the agents, the kubeconfig, and the SAN (alternative names of the API certificate).
- [ ] The HomeLab CA on the nodes (role `opkssh`), because new servers rely on Dex for user login.
- [ ] An encryption method for the backup (contains the token and cluster certificates): a public key of `age` (`k3s_move_backup_age_recipient`) or a password for `gpg` (`k3s_move_backup_passphrase`, better via environment variable). Without either, the playbook aborts, except if forced with `-e k3s_move_backup_unencrypted=true` (not recommended).
- [ ] `oliver` with about 5 GB of free memory. If it has heavy loads, move them beforehand.

## Step by Step

From `ansible/`:

1. **Dry run, no changes made:**

    ```bash
    ansible-playbook -i inventory.ini playbook-k3s-move-controlplane.yml --check --diff
    ```

2. **Actual execution.** With pauses enabled by default, the playbook asks for confirmation before the backup, before
   converting to etcd, before joining `oliver`, before restarting DNS and before removing the source:

    ```bash
    ansible-playbook -i inventory.ini playbook-k3s-move-controlplane.yml
    ```

    Useful variables: `k3s_move_target` (the destination, default `oliver`), `k3s_move_backup_dir` (where the
    backup is saved, default `~/k3s-move-backups` on your machine), `k3s_move_backup_age_recipient` or
    `k3s_move_backup_passphrase` (encryption), `k3s_move_agent_token` (if you want to set the *agent-token* instead of
    generating it), `k3s_move_drain_source`, `k3s_move_rotate_secrets`, `k3s_move_allow_unsynced` and
    `k3s_move_confirm=false` for non-interactive (not recommended).

3. **Pause points.**
    - After the backup: open the file and check its checksum before proceeding.
    - Before converting: this is the step that **cannot be undone without rollback**.
    - After joining `oliver`: `kubectl get nodes` should show two servers.
    - After restarting DNS: `dig +short k3s.homelab.local @192.168.20.5` should return the IP of `oliver`.

!!! tip "If something doesn't convince you, stop"
    Each pause allows aborting with `Ctrl+C`. If the playbook is interrupted after stage 3, do not resume with
    `--tags` loose: stages 4 and 6 need the token obtained in stage 3, within the same execution.

Upon completion, the playbook **does not modify the inventory**: you do it as explained below. The agents stop using
the server token and switch to their own **agent-token**, which is stored in `<k3s_move_backup_dir>/agent-token`.

With the move, the new server's hardening measures are also applied: flags `oidc-*` towards Dex (user login, with `--oidc-username-prefix=oidc:` and `--oidc-groups-prefix=oidc:`), `--secrets-encryption` (encryption of Secrets at rest) and the K3s installer verified by checksum instead of `curl | sh`. The admin certificate is kept only for emergencies. See [Authentication Model](../security/modelo-de-autenticacion.md).

## Verification

| What | How |
|---|---|
| Nodes | `kubectl get nodes -o wide`: `oliver` with role `control-plane`, and the three in `Ready` |
| Argo CD | `kubectl -n argocd get applications`: all `Synced` and `Healthy` |
| Longhorn | UI or `kubectl -n longhorn-system get volumes.longhorn.io`: no degraded volumes |
| Kong | `curl -kI https://argocd.homelab.local` responds |
| DNS | `dig +short k3s.homelab.local @192.168.20.5` returns the IP of `oliver` |
| Pods | `kubectl get pods -A` without stuck pods (`Pending`, `CrashLoopBackOff`); those that lived in `deborah` are rescheduled |

## What Changes in the Inventory After

The playbook does not touch these files; edit them manually after finishing (and commit your changes):

- [`inventory.ini`](https://github.com/maceosoft/homelab/blob/main/ansible/inventory.ini): `deborah` changes from
  `[k3s_server]` to `[k3s_agent]` and `oliver` changes from `[k3s_agent]` to `[k3s_server]` (and its `k3s_role`).
- `group_vars/all.yml`: `k3s_api_ip` changes to `192.168.20.7` (the IP of `oliver`) and `k3s_move_done` changes to `true`.
- `host_vars/deborah.yml` and `host_vars/oliver.yml`: K3s labels and options follow `k3s_move_done`;
  `deborah` keeps `workload-tier=heavy` and `oliver` remains `light`.
- Reapply `playbook-bind-dns.yml` to align the zone with `k3s_api_ip`.
- **SUC Plans** (*System Upgrade Controller*, the automatic K3s updater; [`k3s-upgrade/`](https://github.com/maceosoft/gitops/tree/main/k3s-upgrade)): select the control plane by the `node-role.kubernetes.io/control-plane` label, so they do not change and now update first to `oliver`.

Other guides that discuss the control plane: [Remove or Replace a Node](sacar-nodo.md),
[Add a Node](agregar-nodo.md), [Update K3s](actualizar-k3s.md) and the
[Phase 3](../implementacion/fase-3-k3s.md).

## Rollback

Restore the original SQLite in `deborah` from the backup and return `oliver` to agent:

```bash
  # o -e k3s_move_backup_passphrase=...
ansible-playbook -i inventory.ini playbook-k3s-move-controlplane.yml --tags rollback \
  -e k3s_move_backup_stamp=<AAAAMMDDTHHMMSS> \
  -e k3s_move_backup_age_identity=<archivo de identidad age>
```

The mark is the date part of the backup file name in the backup directory. Rollback is four steps, in this order: **1)** DNS points back to `deborah` and waits about 300 seconds for propagation (if not, the agent reinstalled in `oliver` would try to join itself by `k3s.homelab.local`); **2)** the source is restored; **3)** `oliver` returns to agent; **4)** the other agents recover the original token. **All changes to the cluster after the backup are lost**: decide carefully before reverting. If you had already edited the inventory, revert it to its previous state.

## Manual Steps After Completion

1. **Kubeconfig.** Regenerate the one on your machine, which pointed to the old IP:

    ```bash
    ansible-playbook -i inventory.ini playbook-k3s.yml --tags kubeconfig
    ```

2. **Save the migration secrets in 1Password.** The *agent-token* (`<k3s_move_backup_dir>/agent-token`) and the key or password with which you encrypted the backup. The unencrypted backup and the `/root/k3s-move-*` files of the nodes are deleted automatically at the end (`shred`); the only thing left is the encrypted backup on your machine, which is what is used for rollback.
3. **Check Argo CD, Longhorn, and Kong** with the [Verification](#verification) table.
4. **Login permissions with Dex.** The repo `gitops` brings the ClusterRoleBinding
   [`oidc-devops-view`](https://github.com/maceosoft/gitops/blob/main/security/rbac/oidc-devops.yaml)
   (Application `security-rbac`, already active), which gives the ClusterRole `view` (read-only) to the group
   `oidc:maceosoft:devops`. It is harmless until there are OIDC tokens.

    !!! info "Why read-only and not `cluster-admin`"
        Logging in with Dex should not give full cluster control by default: state changes go through Git and
        Argo CD, and the admin certificate is kept for emergencies. If a user needs to write in a namespace, extend with a `RoleBinding` that binds the ClusterRole `edit` to the same group **only in that namespace**, instead of extending the ClusterRoleBinding.

5. **Optional, risk with Calico.** Check that a common service account cannot create global policies (see
   [Optional Checks](../security/modelo-de-autenticacion.md#optional-checks)).

### Logging in with Dex (kubelogin)

With the flags `oidc-*` enabled, you can log in to the API using your GitHub account instead of the admin certificate. Install the `kubelogin` plugin (`kubectl oidc-login`) and request a token:

```bash
kubectl oidc-login get-token \
  --oidc-issuer-url=https://argocd.homelab.local/api/dex \
  --oidc-client-id=kubernetes \
  --oidc-extra-scope=email,groups
```

A browser window opens; the Dex client `kubernetes` is public (PKCE) and receives the response at
`http://localhost:8000` (or, as a fallback, `18000`): those ports must be free on your machine. To use it always, configure a user in your kubeconfig with `exec` pointing to that command.

## Risks

- It is a **single** control plane (no HA, high availability): if `oliver` goes down, the cluster loses its API until it is restored. Running workloads continue to run.
- Switching from SQLite to etcd is a data store change: that's why backup and rollback are part of the procedure, not an extra.

See also [Removing or Replacing a Node](sacar-nodo.md), [Updating K3s](actualizar-k3s.md), and the [Phase 3 — K3s](../implementacion/fase-3-k3s.md).
