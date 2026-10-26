# Runner cache (ARC)

ARC (Actions Runner Controller) runners are ephemeral pods: every job starts
empty. Without a cache, every job downloads Python or Node again, the pip/npm packages, the
Helm charts, the OpenTofu providers and the tools of the `gitops` pipeline.
To avoid that, the runners mount a shared volume at `/cache` that survives
between jobs, except for the `setup-python`/`setup-node` *tool cache* (see below).

!!! note "One cache per organization"
    Each scale set has its own cache: `arc-cache` of 20 GiB in `arc-runners` (org `maceosoft`) and another of 10 GiB in
    `arc-runners-symintel` (old org). Everything below applies to both; run the commands in the matching namespace.

## How it is put together

| Piece | Where | What it does |
|---|---|---|
| PVC `arc-cache` | [`gitops/arc/cache/pvc.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/cache/pvc.yaml) | 20 Gi, `ReadWriteMany` (RWX: several pods at once, on different nodes), StorageClass `longhorn` (served over NFS) |
| Mount and variables | [`gitops/arc/values-scaleset.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/values-scaleset.yaml) | Mounts the volume at `/cache` and points each tool's cache there; an `initContainer` sets the folders to the runner user |
| Cleanup | [`gitops/arc/cache/prune-cronjob.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/cache/prune-cronjob.yaml) | Weekly CronJob (Sunday 04:00) that deletes pip, npm, Helm and XDG files untouched for more than 30 days, and shows the usage |

What is stored and where:

| Folder | Content | Variable |
|---|---|---|
| `/cache/pip`, `/cache/npm` | Downloaded packages | `PIP_CACHE_DIR`, `npm_config_cache` |
| `/cache/helm`, `/cache/xdg` | Helm indexes and charts, generic caches | `HELM_CACHE_HOME`, `XDG_CACHE_HOME` |
| `/cache/tofu-plugins` | OpenTofu providers (per OS and architecture) | `TF_PLUGIN_CACHE_DIR` |
| `/cache/dl` | helm, kustomize, kubeconform, gitleaks and argocd tarballs for the `gitops` pipeline | `RUNNER_CACHE` |

!!! warning "The `setup-python` and `setup-node` tool cache is NOT shared"
    `setup-python` deletes and reinstalls the folder of the version it is going to use. With the tool
    cache on the shared volume, two parallel jobs (for example `render` and
    `security` in `gitops`) stepped on the same folder and failed with `rm: cannot
    remove … Stale file handle`. That is why `RUNNER_TOOL_CACHE` keeps its default
    value (`_work/_tool`, local to each runner) and Python/Node are downloaded in every job
    (~20 s). What is shared is safe in parallel: pip, npm, Helm and the tarballs
    in `/cache/dl` (they are written to a temporary file and renamed).

The cluster mixes `amd64` and `arm64` nodes (`deborah`): that is why anything that depends on the
architecture goes into folders split by it (OpenTofu providers and tarball
names) and is safe to share.

## How reused content is verified

The `gitops` pipeline binaries are not trusted blindly: every job downloads the
checksums file published by the project (a few KB) and the cached tarball is only
used if its `sha256` matches; otherwise it is downloaded again. The rest of the caches (tool
cache, pip, npm) cannot be verified this way.

!!! warning "Risk: cache shared with a public repo"
    The scale set also serves public repos (for example `homelab`). A PR from a
    fork could leave a tampered package in the cache that a job of a
    private repo then uses. Mitigation: in the `maceosoft` org, *Settings → Actions → General →
    Fork pull request workflows*, require **approval for all outside
    collaborators**. If you do not need `homelab` to be public, making it private removes the
    risk.

## Verify that it works

1. The volume is bound and the runners mount it:

    ```bash
    # STATUS: Bound
    kubectl -n arc-runners get pvc arc-cache
    kubectl -n arc-runners get cronjob arc-cache-prune
    ```

2. Run the same workflow twice in a row. In the second run, `pip install` says
   `Using cached …` and the `gitops` tools step does not download tarballs
   (it takes seconds).
3. Check how much space it takes (with a temporary pod; the runner no longer exists when the job ends):

    ```bash
    kubectl -n arc-runners run cache-du --rm -it --restart=Never --image=busybox:1.37 \
      --overrides='{"spec":{"containers":[{"name":"cache-du","image":"busybox:1.37","command":["sh","-c","du -sh /cache/*; df -h /cache | tail -1"],"volumeMounts":[{"name":"c","mountPath":"/cache"}]}],"volumes":[{"name":"c","persistentVolumeClaim":{"claimName":"arc-cache"}}]}}'
    ```

## Empty the cache

It is safe: jobs download again whatever is missing. Use a temporary pod like the one
above but with `rm -rf /cache/*`, or delete the PVC (Argo CD recreates it):

```bash
kubectl -n arc-runners delete pvc arc-cache
```

Do it if you suspect a tampered or corrupted cache.

## If it fails

| Symptom | Check |
|---|---|
| The runners do not start (`Pending`) | `kubectl -n arc-runners describe pvc arc-cache`: Longhorn must be `Healthy` and the nodes must have `nfs-common` (`k3s_prereqs` role) |
| The job says `Permission denied` on `/cache` | The `initContainer cache-perms` could not `chown` (NFS with root squash): `kubectl -n arc-runners logs <pod> -c cache-perms` |
| `rm: cannot remove … Stale file handle` on `/cache/…` | Two jobs writing the same volume folder: do not share caches there that get deleted and reinstalled (like the tool cache); if there is corrupted data, empty that folder |
| `Checksum incorrecto` in the `gitops` pipeline | A corrupted download or a tampered cache: empty `/cache/dl` and retry |
| The volume fills up | `df -h /cache` from the temporary pod; grow the PVC (Longhorn allows expansion) or empty `/cache/xdg` or `/cache/pip` |
