# Caché de los runners (ARC)

Los runners de ARC (Actions Runner Controller) son pods efímeros: cada job arranca
vacío. Sin caché, cada job vuelve a bajar Python o Node, los paquetes pip/npm, los
charts de Helm, los providers de OpenTofu y las herramientas del pipeline de `gitops`.
Para evitarlo, los runners montan un volumen compartido en `/cache` que sobrevive
entre jobs, excepto el *tool cache* de `setup-python`/`setup-node` (ver abajo).

!!! note "Una caché por organización"
    Cada scale set tiene su propia caché: `arc-cache` de 20 GiB en `arc-runners` (org `maceosoft`) y otra de 10 GiB en
    `arc-runners-symintel` (org antigua). Todo lo que sigue vale para las dos; los comandos se corren en el namespace que corresponda.

## Cómo está armado

| Pieza | Dónde | Qué hace |
|---|---|---|
| PVC `arc-cache` | [`gitops/arc/cache/pvc.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/cache/pvc.yaml) | 20 Gi, `ReadWriteMany` (RWX: varios pods a la vez, en nodos distintos), StorageClass `longhorn` (se sirve por NFS) |
| Montaje y variables | [`gitops/arc/values-scaleset.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/values-scaleset.yaml) | Monta el volumen en `/cache` y apunta las cachés de cada herramienta ahí; un `initContainer` deja las carpetas con el usuario del runner |
| Limpieza | [`gitops/arc/cache/prune-cronjob.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/cache/prune-cronjob.yaml) | CronJob semanal (domingo 04:00) que borra archivos sin tocar hace más de 30 días de pip, npm, Helm y XDG, y muestra el uso |

Qué se guarda y dónde:

| Carpeta | Contenido | Variable |
|---|---|---|
| `/cache/pip`, `/cache/npm` | Paquetes descargados | `PIP_CACHE_DIR`, `npm_config_cache` |
| `/cache/helm`, `/cache/xdg` | Índices y charts de Helm, cachés genéricas | `HELM_CACHE_HOME`, `XDG_CACHE_HOME` |
| `/cache/tofu-plugins` | Providers de OpenTofu (por sistema y arquitectura) | `TF_PLUGIN_CACHE_DIR` |
| `/cache/dl` | Tarballs de helm, kustomize, kubeconform, gitleaks y argocd del pipeline de `gitops` | `RUNNER_CACHE` |

!!! warning "El tool cache de `setup-python` y `setup-node` NO se comparte"
    `setup-python` borra y reinstala la carpeta de la versión que va a usar. Con el tool
    cache en el volumen compartido, dos jobs en paralelo (por ejemplo `render` y
    `security` de `gitops`) se pisaban la misma carpeta y fallaban con `rm: cannot remove … Stale file handle`. Por eso `RUNNER_TOOL_CACHE` queda en el valor por
    defecto (`_work/_tool`, local a cada runner) y Python/Node se descargan en cada job
    (~20 s). Lo que sí se comparte es seguro en paralelo: pip, npm, Helm y los tarballs
    de `/cache/dl` (se escriben a un archivo temporal y se renombran).

El clúster mezcla nodos `amd64` y `arm64` (`deborah`): por eso lo que depende de la
arquitectura va en carpetas separadas por ella (providers de OpenTofu y nombres de
tarball) y es seguro compartirlo.

## Cómo se verifica lo que se reutiliza

Los binarios del pipeline de `gitops` no se confían a ciegas: en cada job se baja el
archivo de checksums que publica el proyecto (unos KB) y el tarball cacheado solo se
usa si su `sha256` coincide; si no, se vuelve a descargar. El resto de cachés (tool
cache, pip, npm) no se puede verificar así.

!!! warning "Riesgo: caché compartida con un repo público"
    El scale set atiende también a repos públicos (por ejemplo `homelab`). Un PR de un
    fork podría dejar en la caché un paquete alterado que después use un job de un
    repo privado. Mitigación: en la org `maceosoft`, *Settings → Actions → General →
    Fork pull request workflows*, exige **aprobación para todos los colaboradores
    externos**. Si no necesitas que `homelab` sea público, hacerlo privado elimina el
    riesgo.

## Verificar que funciona

1. El volumen está enlazado y los runners lo montan:

    ```bash
    # STATUS: Bound
    kubectl -n arc-runners get pvc arc-cache
    kubectl -n arc-runners get cronjob arc-cache-prune
    ```

2. Corre dos veces seguidas el mismo workflow. En el segundo, `pip install` dice
   `Using cached …` y el paso de herramientas de `gitops` no descarga tarballs
   (tarda segundos).
3. Mira cuánto ocupa (con un pod temporal, el runner ya no existe al terminar el job):

    ```bash
    kubectl -n arc-runners run cache-du --rm -it --restart=Never --image=busybox:1.37 \
      --overrides='{"spec":{"containers":[{"name":"cache-du","image":"busybox:1.37","command":["sh","-c","du -sh /cache/*; df -h /cache | tail -1"],"volumeMounts":[{"name":"c","mountPath":"/cache"}]}],"volumes":[{"name":"c","persistentVolumeClaim":{"claimName":"arc-cache"}}]}}'
    ```

## Vaciar la caché

Es seguro: los jobs vuelven a descargar lo que falte. Con un pod temporal como el de
arriba pero con `rm -rf /cache/*`, o borrando el PVC (Argo CD lo recrea):

```bash
kubectl -n arc-runners delete pvc arc-cache
```

Hazlo si sospechas de una caché alterada o corrupta.

## Si falla

| Síntoma | Revisar |
|---|---|
| Los runners no arrancan (`Pending`) | `kubectl -n arc-runners describe pvc arc-cache`: Longhorn debe estar `Healthy` y los nodos tener `nfs-common` (rol `k3s_prereqs`) |
| El job dice `Permission denied` en `/cache` | El `initContainer cache-perms` no pudo hacer `chown` (NFS con squash de root): `kubectl -n arc-runners logs <pod> -c cache-perms` |
| `rm: cannot remove … Stale file handle` en `/cache/…` | Dos jobs escribiendo la misma carpeta del volumen: no compartas ahí cachés que se borran y reinstalan (como el tool cache); si hay datos corruptos, vacía esa carpeta |
| `Checksum incorrecto` en el pipeline de `gitops` | Una descarga corrupta o una caché alterada: vacía `/cache/dl` y reintenta |
| El volumen se llena | `df -h /cache` desde el pod temporal; sube el tamaño del PVC (Longhorn permite expandir) o vacía `/cache/xdg` o `/cache/pip` |
