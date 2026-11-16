# Runner Cache (ARC)

ARC (Actions Runner Controller) runners are ephemeral pods: each job starts
empty. Without a cache, every job downloads Python or Node again, the pip/npm packages, the
Helm charts, the OpenTofu providers, and the tools for the `gitops` pipeline.
To avoid this, the runners mount a shared volume at `/cache` that persists
between jobs, except for the `setup-python`/`setup-node` *tool cache* (see below).

!!! note "One cache per organization"
    Each scale set has its own cache: a 20 GiB `arc-cache` in `arc-runners` (org `maceosoft`) and another 10 GiB one in
    `arc-runners-symintel` (old org). Everything below applies to both; run the commands in the corresponding namespace.

## How it's set up

| Piece | Where | What it does |
|---|---|---|
| PVC `arc-cache` | [`gitops/arc/cache/pvc.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/cache/pvc.yaml) | 20 Gi, `ReadWriteMany` (RWX: several pods at once, on different nodes), StorageClass `longhorn` (served over NFS) |
| Mount and variables | [`gitops/arc/values-scaleset.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/values-scaleset.yaml) | Mounts the volume at `/cache` and points each tool's cache there; a `initContainer` leaves the folders owned by the runner user |
| Cleanup | [`gitops/arc/cache/prune-cronjob.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/cache/prune-cronjob.yaml) | Weekly CronJob (Sunday 04:00) that deletes pip, npm, Composer, Helm and XDG files not touched in over 30 days, and shows usage |

What is stored and where:

| Folder | Contents | Variable |
|---|---|---|
| `/cache/pip`, `/cache/npm`, `/cache/composer` | Downloaded packages | `PIP_CACHE_DIR`, `npm_config_cache`, `COMPOSER_CACHE_DIR` |
| `/cache/helm`, `/cache/xdg` | Helm indexes and charts, generic caches | `HELM_CACHE_HOME`, `XDG_CACHE_HOME` |
| `/cache/tofu-plugins` | OpenTofu providers (per system and architecture) | `TF_PLUGIN_CACHE_DIR` |
| `/cache/dl` | Tarballs of helm, kustomize, kubeconform, gitleaks and argocd from the `gitops` pipeline | `RUNNER_CACHE` |

!!! warning "The `setup-python` and `setup-node` tool cache is NOT shared"
    `setup-python` deletes and reinstalls the folder of the version it is going to use. With the tool
    cache on the shared volume, two parallel jobs (for example `render` and
    `security` from `gitops`) overwrote the same folder and failed with `rm: cannot remove … Stale file handle`. That is why `RUNNER_TOOL_CACHE` stays at the default
    value (`_work/_tool`, local to each runner) and Python/Node are downloaded in every job
    (~20 s). What is shared is safe in parallel: pip, npm, Helm and the
    `/cache/dl` tarballs (they are written to a temporary file and renamed).

The cluster mixes `amd64` and `arm64` nodes (`deborah`): that is why anything that depends on the
architecture goes in folders separated by it (OpenTofu providers and tarball
names) and is safe to share.

## Docker and runners with PHP

All runners include Docker with a privileged `dind` sidecar, so their namespaces use `enforce=privileged`. It is defined in [`gitops/arc/values-scaleset.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/values-scaleset.yaml), with an MTU of 1400 because Calico uses 1450: with a larger MTU, TLS connections from containers hang.

The `arc-php-84` scale set uses the `ghcr.io/symintel/ci-php` image, with PHP 8.4, Composer, `lftp` and PostgreSQL 16. It shares namespace, Secrets and cache with `arc-runners-symintel`. Its values file repeats `containers`: any change to that part of the template must be copied there.

!!! warning "Forks"
    A job with Docker has high privileges on its node. `homelab` is public, so only collaborators can open PRs and no fork can trigger workflows on these runners. Don't relax that setting.

## How reused content is verified

The `gitops` pipeline binaries are not blindly trusted: in each job the
checksums file published by the project (a few KB) is downloaded, and the cached tarball is only
used if its `sha256` matches; otherwise it is downloaded again. The other caches (tool
cache, pip, npm) can't be verified this way.

!!! warning "Risk: shared cache with a public repo"
    The scale set also serves public repos (for example `homelab`). A PR from a
    fork could leave a tampered package in the cache that a job from a
    private repo then uses. Mitigation: in the `maceosoft` org, under *Settings → Actions → General →
    Fork pull request workflows*, require **approval for all outside
    collaborators**. If you don't need `homelab` to be public, making it private eliminates the
    risk.

    === "🖱️ From the UI"

        In the `maceosoft` org: *Settings → Actions → General → Fork pull request workflows*, approval option
        for **all outside collaborators**.

    === "⌨️ From the console"

        With `gh` as the org owner (the `admin:org` permission is requested once with `gh auth refresh -s admin:org`):

        ```bash
        gh api -X PUT orgs/maceosoft/actions/permissions/fork-pr-contributor-approval \
          -f approval_policy=all_external_contributors
        gh api orgs/maceosoft/actions/permissions/fork-pr-contributor-approval
        ```

## Verify that it works

1. The volume is bound and the runners mount it:

    ```bash
    # STATUS: Bound
    kubectl -n arc-runners get pvc arc-cache
    kubectl -n arc-runners get cronjob arc-cache-prune
    ```

2. Run the same workflow twice in a row. On the second run, `pip install` says
   `Using cached …` and the `gitops` tools step doesn't download tarballs
   (it takes seconds).
3. Check how much space it uses (with a temporary pod, since the runner no longer exists once the job finishes):

    ```bash
    kubectl -n arc-runners run cache-du --rm -it --restart=Never --image=busybox:1.37 \
      --overrides='{"spec":{"containers":[{"name":"cache-du","image":"busybox:1.37","command":["sh","-c","du -sh /cache/*; df -h /cache | tail -1"],"volumeMounts":[{"name":"c","mountPath":"/cache"}]}],"volumes":[{"name":"c","persistentVolumeClaim":{"claimName":"arc-cache"}}]}}'
    ```

## Emptying the cache

It's safe: jobs will download whatever is missing again. Use a temporary pod like the one
above but with `rm -rf /cache/*`, or delete the PVC (Argo CD recreates it):

```bash
kubectl -n arc-runners delete pvc arc-cache
```

Do this if you suspect the cache is tampered with or corrupted.

## If it fails

| Symptom | Check |
|---|---|
| Runners don't start (`Pending`) | `kubectl -n arc-runners describe pvc arc-cache`: Longhorn must be `Healthy` and the nodes must have `nfs-common` (role `k3s_prereqs`) |
| The job says `Permission denied` in `/cache` | The `initContainer cache-perms` couldn't do `chown` (NFS with root squash): `kubectl -n arc-runners logs <pod> -c cache-perms` |
| `rm: cannot remove … Stale file handle` in `/cache/…` | Two jobs writing to the same volume folder: don't share caches there that get deleted and reinstalled (like the tool cache); if the data is corrupted, empty that folder |
| `Checksum incorrecto` in the `gitops` pipeline | A corrupted download or a tampered cache: empty `/cache/dl` and retry |
| The volume fills up | `df -h /cache` from the temporary pod; increase the PVC size (Longhorn supports expansion) or empty `/cache/xdg` or `/cache/pip` |
