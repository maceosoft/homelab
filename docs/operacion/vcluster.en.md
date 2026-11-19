# Frequent vCluster Operations

Everyday commands with [vCluster](../vcluster/index.md) open source. All use your GitHub kubeconfig
([Access Kubernetes with GitHub](acceso-kubernetes.md)) and the `vcluster` 0.38.0 CLI (installation in
[Phase 5](../implementacion/fase-5-vcluster.md#before-you-start)). In the examples the vCluster is named `prueba` and lives in
the namespace `vcluster-prueba`.

```bash
export KUBECONFIG=~/.kube/homelab-github.yaml
```

## Create

```bash
VALUES=~/src/maceosoft/gitops/addons/cluster/vcluster/values/demo.yaml   # tu copia de gitops, en main y al día
vcluster create prueba -n vcluster-prueba -f "$VALUES" --chart-version 0.38.0 --connect=false
kubectl -n vcluster-prueba rollout status statefulset/prueba --timeout=300s
```

The `gitops` repo is private: values are read from your local copy (not from `raw.githubusercontent.com`, which returns
404). Takes about a minute. Without the values (or without `storageClass`), the volume ends up `Pending`: the cluster has no
default StorageClass. For one managed by Argo CD, see [Phase 5](../implementacion/fase-5-vcluster.md#run).

## Enable the GitOps vCluster (`vcluster-demo`)

For one that gets declared in git and maintained by Argo CD. The example Application is turned off in `gitops`.

1. **Enable it in git** (in your copy of `gitops`, on a new branch):

    ```bash
    cd ~/src/maceosoft/gitops
    git checkout main && git pull
    git checkout -b vcluster/activar-demo
    git mv bootstrap/components/apagadas/vcluster-demo.yaml bootstrap/components/vcluster-demo.yaml
    git commit -m "vCluster: activar vcluster-demo"
    ```

    Also remove its line from the "Optional applications that are NOT active" rule in `renovate.json5`, so that
    Renovate notifies about new chart versions. Push the branch, open the PR and merge it.

2. **Wait for the Application to appear.** The ApplicationSet `homelab` creates it in one or two minutes with the
   wave `manual`: it ends up `OutOfSync` and `Missing`, without deploying anything, because it has no auto-sync.

    ```bash
    KUBECONFIG=~/.kube/homelab-k3s.yaml kubectl -n argocd get application vcluster-demo
    ```

3. **Sync it manually.**

    === "🖱️ From the UI"

        Open [`https://argocd.homelab.local`](https://argocd.homelab.local), sign in with GitHub, find the Application
        `vcluster-demo` and click **Sync** → **Synchronize**.

    === "⌨️ From the console"

        With the Argo CD CLI (`brew install argocd`). The `admin` user is disabled: you sign in with GitHub
        (`--sso` opens the browser).

        ```bash
        argocd login argocd.homelab.local --sso --grpc-web
        argocd app sync vcluster-demo
        argocd app wait vcluster-demo --health --timeout 300
        ```

4. **Verify and enter.** Takes about a minute to become `Synced` and `Healthy`:

    ```bash
    export KUBECONFIG=~/.kube/homelab-github.yaml
    kubectl -n argocd get application vcluster-demo     # Synced / Healthy
    vcluster list                                       # demo   vcluster-demo   Running
    vcluster connect demo -n vcluster-demo -- kubectl get ns
    ```

Each subsequent change (another chart version, other values) is done in git and synced manually again. To turn it off, see [Delete](#delete).

## List existing ones

```bash
vcluster list
```

Shows name, namespace, status (`Running`, `Paused`), version and age.

For details of one (version, images, storage and the config it was created with):

```bash
vcluster describe prueba -n vcluster-prueba
```

## Enter

**A one-off command** (opens the tunnel, runs the command and closes it):

```bash
vcluster connect prueba -n vcluster-prueba -- kubectl get ns
```

**A work session:** in one terminal keep a tunnel open to the vCluster Service on a fixed port; in another,
generate its kubeconfig pointing to that port and use it. This way your GitHub kubeconfig stays untouched:

```bash
# Terminal 1 (queda abierta mientras trabajas)
kubectl -n vcluster-prueba port-forward svc/prueba 11443:443

# Terminal 2
vcluster connect prueba -n vcluster-prueba --local-port 11443 --print --silent > ~/.kube/vcluster-prueba.yaml
chmod 600 ~/.kube/vcluster-prueba.yaml
kubectl --kubeconfig ~/.kube/vcluster-prueba.yaml get ns
```

With `--kubeconfig` on each command (or an alias: `alias kvc='kubectl --kubeconfig ~/.kube/vcluster-prueba.yaml'`), the
rest of the terminal keeps pointing to the host cluster with your GitHub kubeconfig, which is what the other
operations on this page use.

To exit, `Ctrl+C` in terminal 1. The file `~/.kube/vcluster-prueba.yaml` contains a vCluster admin key: don't share it and delete it when you're done (`rm ~/.kube/vcluster-prueba.yaml`).

`vcluster connect prueba -n vcluster-prueba` with no extra arguments also opens the tunnel, but adds the vCluster context to the kubeconfig you're using and sets it as current; to go back, `vcluster disconnect`.

## Verify it works

Inside the vCluster:

```bash
vcluster connect prueba -n vcluster-prueba -- sh -c '
  kubectl create deployment web --image=nginx:1.29-alpine &&
  kubectl expose deployment web --port 80 &&
  kubectl rollout status deploy/web --timeout=120s &&
  kubectl run curl --image=curlimages/curl:8.17.0 --rm -i --restart=Never -- \
    curl -s -o /dev/null -w "HTTP %{http_code}\n" http://web.default.svc'
```

It must respond `HTTP 200`. On the host you'll see the pods with the translated name:

```bash
kubectl -n vcluster-prueba get pods
# web-7fbc579fd4-9l5hg-x-default-x-prueba   1/1   Running
```

## Pause and resume

Pausing scales the vCluster control plane and workloads to zero (frees CPU and RAM) and preserves data in its volume:

```bash
vcluster pause prueba -n vcluster-prueba
kubectl -n vcluster-prueba get pods      # No resources found
vcluster resume prueba -n vcluster-prueba
kubectl -n vcluster-prueba rollout status statefulset/prueba --timeout=300s
```

On resume, what you created inside is still there.

## Backup and restore

A snapshot saves everything inside the vCluster (its database: Deployments, ConfigMaps, Secrets…). It does
not save the contents of app volumes.

```bash
# Respaldar (tarda segundos)
vcluster snapshot create prueba container:///data/respaldo.tar.gz -n vcluster-prueba
kubectl -n vcluster-prueba logs prueba-0 -c syncer --since=2m | grep -i snapshot   # "Successfully wrote snapshot"

# Restaurar: pausa el vCluster, reemplaza su base de datos y lo reanuda
vcluster restore prueba container:///data/respaldo.tar.gz -n vcluster-prueba
kubectl -n vcluster-prueba rollout status statefulset/prueba --timeout=300s   # esperar a que vuelva
```

`container://` saves the file **inside the vCluster's own volume**: useful to roll back a change, but if
you delete the vCluster it's lost with it. For a real backup, copy it to your machine after creating it, and upload it
back before restoring (with the vCluster `Running`: while it restarts, `kubectl cp` responds
`container not found ("syncer")`):

```bash
kubectl -n vcluster-prueba cp -c syncer prueba-0:/data/respaldo.tar.gz ./vcluster-prueba-respaldo.tar.gz
kubectl -n vcluster-prueba cp -c syncer ./vcluster-prueba-respaldo.tar.gz prueba-0:/data/respaldo.tar.gz
```

`vcluster snapshot get prueba container:///…` responds `No snapshot found` even if the snapshot exists: with the target
`container://` it doesn't list them. Confirm via the log (above) or with
`kubectl -n vcluster-prueba exec prueba-0 -c syncer -- ls -la /data/`.

## View logs and status

```bash
kubectl -n vcluster-prueba logs statefulset/prueba -c syncer --tail=50     # API y syncer del vCluster
kubectl -n vcluster-prueba get pods,pvc
vcluster connect prueba -n vcluster-prueba -- kubectl get events -A --sort-by=.lastTimestamp
```

## Update

Use the same version in the CLI and in the chart. For a vCluster created with the CLI (`--connect=false`: without it, the CLI
connects at the end and leaves the vCluster as the active context in your kubeconfig):

```bash
vcluster create prueba -n vcluster-prueba -f "$VALUES" --chart-version <nueva> --upgrade --connect=false
kubectl -n vcluster-prueba rollout status statefulset/prueba --timeout=300s
```

For one managed by Argo CD, change `targetRevision` in its Application in `gitops` (Renovate notifies about new
versions when the app is active). Before upgrading major version, read the
[release notes](https://github.com/loft-sh/vcluster/releases).

## Delete

```bash
vcluster delete prueba -n vcluster-prueba --delete-namespace
vcluster list
```

Deletes the control plane, synced workloads, the Longhorn volume and the namespace. For one managed by Argo
CD, remove its file from `bootstrap/components/` (or move it to `apagadas/`), delete the Application and then the namespace,
which Argo CD doesn't delete:

```bash
kubectl -n argocd delete application vcluster-demo
kubectl delete ns vcluster-demo
```

## Telemetry

The CLI and vCluster send anonymous usage data to Loft (the company behind vCluster). To turn it off in your machine's CLI:

```bash
vcluster telemetry disable
```

## If it fails

| Symptom | Cause |
|---|---|
| `Forbidden` on create | You're not using the GitHub kubeconfig or you're not in the `devops` team (`kubectl auth whoami`) |
| `prueba-0` in `Pending` | Missing `storageClass` in values |
| `vcluster connect` hangs | The vCluster is `Paused` or its pod isn't ready (`vcluster list`) |
| `address already in use` | The `--local-port` port is busy: use another |
| An app pod won't start inside | Check it on the host: `kubectl -n vcluster-prueba describe pod <nombre>-x-<ns>-x-prueba` |
