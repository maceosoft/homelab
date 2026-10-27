# ARC runner cache

ARC (Actions Runner Controller) runners are ephemeral pods: every job starts
empty. Without a cache, each job re-downloads Python or Node, pip/npm packages,
Helm charts, OpenTofu providers, and the `gitops` pipeline tools.
To avoid this, runners mount a shared volume at `/cache` that persists
across jobs, except for the `setup-python`/`setup-node` *tool cache* (see below).

!!! note "One cache per organization"
    Each scale set has its own cache: `arc-cache` of 20 GiB at `arc-runners` (org `maceosoft`) and another 10 GiB at
    `arc-runners-symintel` (legacy org). Everything that follows applies to both; commands run in the corresponding namespace.

## How it is built

| Piece | Where | What it does |
|---|---|---|
| PVC `arc-cache` | [`gitops/arc/cache/pvc.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/cache/pvc.yaml) | 20 Gi, `ReadWriteMany` (RWX: multiple pods at once, on different nodes), StorageClass `longhorn` (served via NFS) |
| Mount & variables | [`gitops/arc/values-scaleset.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/values-scaleset.yaml) | Mounts the volume at `/cache` and points each tool's cache there; an `initContainer` leaves the folders owned by the runner user |
| Cleanup | [`gitops/arc/cache/prune-cronjob.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/cache/prune-cronjob.yaml) | Weekly CronJob (Sunday 04:00) that deletes files untouched for more than 30 days from pip, npm, Helm, and XDG, and shows usage |

What is stored and where:

| Folder | Content | Variable |
|---|---|---|
| `/cache/pip`, `/cache/npm` | Downloaded packages | `PIP_CACHE_DIR`, `npm_config_cache` |
| `/cache/helm`, `/cache/xdg` | Helm indexes and charts, generic caches | `HELM_CACHE_HOME`, `XDG_CACHE_HOME` |
| `/cache/tofu-plugins` | OpenTofu providers (per OS and architecture) | `TF_PLUGIN_CACHE_DIR` |
| `/cache/dl` | Tarballs of helm, kustomize, kubeconform, gitleaks, and argocd from the `gitops` pipeline | `RUNNER_CACHE` |

!!! warning "The `setup-python` and `setup-node` tool cache is NOT shared"
    `setup-python` deletes and reinstalls the folder for the version it will use. With the
    tool cache on the shared volume, two parallel jobs (e.g., `render` and
    `security` from `gitops`) would stomp on the same folder and fail with `rm: cannot remove … Stale file handle`. That's why `RUNNER_TOOL_CACHE` stays at the
    default (`_work/_tool`, local to each runner) and Python/Node are downloaded on every job
    (~20 s). What *is* shared is parallel-safe: pip, npm, Helm, and the `/cache/dl` tarballs
    (written to a temp file and renamed).

The cluster mixes `amd64` and `arm64` nodes (`deborah`): that's why
architecture-dependent content lives in separate folders by architecture (OpenTofu
providers and tarball names) and is safe to share.

## How reuse is verified

The `gitops` pipeline binaries are not trusted blindly: in each job the project's
published checksums file (a few KB) is downloaded, and the cached tarball is only
used if its `sha256` matches; otherwise it is re-downloaded. The rest of the caches
(tool cache, pip, npm) cannot be verified this way.

!!! warning "Risk: shared cache with a public repo"
    The scale set also serves public repos (e.g., `homelab`). A PR from a fork
    could leave a tampered package in the cache that a private repo job later uses.
    Mitigation: in org `maceosoft`, *Settings → Actions → General →
    Fork pull request workflows*, require **approval for all outside
    collaborators**. If you don't need `homelab` to be public, making it private
    eliminates the risk.

    === "🖱️ From the UI"

        In org `maceosoft`: *Settings → Actions → General → Fork pull request workflows*, approval option
        for **all outside collaborators**.

    === "⌨️ From the console"

        With `gh` as org owner (the `admin:org` permission is granted once via `gh auth refresh -s admin:org`):

        ```bash
        gh api -X PUT orgs/maceosoft/actions/permissions/fork-pr-contributor-approval \
          -f approval_policy=all_external_contributors
        gh api orgs/maceosoft/actions/permissions/fork-pr-contributor-approval
        ```

## Verify it works

1. The volume is bound and runners mount it:

    ```bash
    # STATUS: Bound
    kubectl -n arc-runners get pvc arc-cache
    kubectl -n arc-runners get cronjob arc-cache-prune
    ```

2. Run the same workflow twice in a row. On the second run, `pip install` says
   `Using cached …` and the `gitops` tools step does not download tarballs
   (takes seconds).
3. Check how much space it uses (with a temp pod, the runner is gone once the job finishes):

    ```bash
    kubectl -n arc-runners run cache-du --rm -it --restart=Never --image=busybox:1.37 \
      --overrides='{"spec":{"containers":[{"name":"cache-du","image":"busybox:1.37","command":["sh","-c","du -sh /cache/*; df -h /cache | tail -1"],"volumeMounts":[{"name":"c","mountPath":"/cache"}]}],"volumes":[{"name":"c","persistentVolumeClaim":{"claimName":"arc-cache"}}]}}'
    ```

## Clear the cache

It's safe: jobs will re-download what's missing. With a temp pod like the one
above but using `rm -rf /cache/*`, or by deleting the PVC (Argo CD recreates it):

```bash
kubectl -n arc-runners delete pvc arc-cache
```

Do this if you suspect a tampered or corrupted cache.

## If it fails

| Symptom | Check |
|---|---|
| Runners won't start (`Pending`) | `kubectl -n arc-runners describe pvc arc-cache`: Longhorn must be `Healthy` and nodes must have `nfs-common` (role `k3s_prereqs`) |
| Job says `Permission denied` in `/cache` | The `initContainer cache-perms` couldn't `chown` (NFS with root squash): `kubectl -n arc-runners logs <pod> -c cache-perms` |
| `rm: cannot remove … Stale file handle` in `/cache/…` | Two jobs writing the same volume folder: don't share caches that delete and reinstall (like the tool cache) there; if data is corrupt, clear that folder |
| `Checksum incorrecto` in the `gitops` pipeline | A corrupt download or a tampered cache: clear `/cache/dl` and retry |
| Volume fills up | `df -h /cache` from the temp pod; increase PVC size (Longhorn allows expansion) or clear `/cache/xdg` or `/cache/pip` |
