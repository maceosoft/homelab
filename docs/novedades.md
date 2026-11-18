# Novedades

Lo que se ha ido sumando al HomeLab, de lo más reciente a lo más antiguo. Las tres últimas también aparecen en el
[inicio](index.md).

<!--
Para agregar una novedad: escríbela arriba de todo, dentro del bloque "recientes", y pasa la más antigua de ese bloque
justo debajo del marcador de cierre. El inicio (index.md) incluye solo lo que está dentro del bloque, con
pymdownx.snippets. Una línea de fecha y título en negrita, dos o tres frases y un enlace a la página que lo explica.
-->

<!-- --8<-- [start:recientes] -->
- **18 nov 2026 · CAPN funciona.** Los clústeres de Kubernetes con nodos en Incus (Cluster API) ya arrancan en el
  HomeLab: la API queda en una IP fija con `kube-vip` en vez de la IPv6 que la dejaba inalcanzable. Se crean a mano,
  en unos 2 minutos, y la guía de operaciones (crear, escalar, actualizar, borrar) se probó comando por comando.
  [Operaciones frecuentes de CAPN](operacion/capn.md).
- **18 nov 2026 · DNS automático.** Lo que se crea se registra solo en el DNS: las apps publicadas en Kubernetes
  (ExternalDNS), las instancias de Incus en `ovn-lan` (`<instancia>.ovn.homelab.local`) y los nodos del inventario
  (Ansible). Cada uno escribe con su propia llave y BIND impide que uno pise los nombres del otro.
  [DNS automático](networking/dns-automatico.md).
- **18 nov 2026 · vCluster open source en vez de vCluster Platform.** La interfaz web de vCluster no sirve sin pagar:
  su plan gratis no incluye el login con GitHub. Ahora los clústeres virtuales se crean con el CLI `vcluster` o con una
  Application de Argo CD, y se entra con la misma cuenta de GitHub que el resto del clúster.
  [Operaciones frecuentes de vCluster](operacion/vcluster.md).
<!-- --8<-- [end:recientes] -->
- **17 nov 2026 · Kubernetes con login de GitHub y Secrets cifrados.** El API de K3s ahora acepta el login con
  GitHub a través de Dex: `kubectl` abre el navegador y el team `devops` entra con acceso total, sin copiar el
  certificado de administrador. Los Secrets del clúster quedaron cifrados en disco, y el certificado del API acepta
  el nombre `k3s.homelab.local`.
  [Entrar a Kubernetes con GitHub](operacion/acceso-kubernetes.md).
- **17 nov 2026 · Respaldos de PostgreSQL en Incus.** El PostgreSQL compartido de la plataforma tendrá sus respaldos
  en un bucket de Incus en `invincible`, publicado por S3 (Simple Storage Service) con un certificado de la CA propia
  del HomeLab. Un proxy delante evita cambiar el certificado de la API de Incus, y las contraseñas y llaves salen de
  1Password. [PostgreSQL y respaldos en Incus](storage/postgres.md).
- **17 nov 2026 · Nueva estructura del repo `gitops`.** Cada app de Argo CD es ahora un archivo en
  `bootstrap/components/`: activarla o apagarla es mover el archivo a `apagadas/`, sin volver a aplicar nada. El
  ApplicationSet `homelab` las despliega por olas (cada ola espera a que la anterior esté sana) y se puede pausar una
  app sin PR. Los manifiestos pasaron a `addons/<área>/` (red, seguridad, monitoreo, IA…).
  [Catálogo GitOps](gitops/index.md).
- **17 nov 2026 · Runners sin credenciales en su entorno.** Los runners de GitHub Actions de `maceosoft` ya no cargan
  la App de OpenTofu, las credenciales FTP ni el token de Argo CD: cualquier job, incluido el de un PR, podía leerlos.
  El token del diff de `gitops` llega ahora como secreto de GitHub Actions solo al paso que lo usa, y vence a los 90
  días. [Pipeline de gitops](operacion/pipeline-gitops.md#activar-el-diff-contra-el-cluster-una-vez).
- **15 nov 2026 · La IA pasa a Claude y NVIDIA.** Ollama quedó pausado en todos los nodos porque los calentaba
  demasiado. Ahora cada alerta llega a Discord con un resumen de Claude, y Open WebUI conversa con Claude y con modelos
  abiertos de NVIDIA. Las claves viven en 1Password, como el resto de los secretos.
  [Asistente de IA](operacion/ia-ollama.md).
- **10 nov 2026 · Temperaturas y NVMe vigilados.** El NVMe (disco SSD por PCIe) de `deborah`, sin disipador, se cayó del bus por calor al
  copiarle datos: quedó fuera de uso hasta tener disipador y ahora hay alertas de temperatura de NVMe y de disco
  desaparecido. Un script muestra todos los sensores de cada nodo.
  [Salud de los discos](operacion/salud-de-discos.md#nvme).
- **8 nov 2026 · Un cuarto nodo: `eve`.** Una MacBook Pro 16" de 2019 con chip T2 (el coprocesador de seguridad de
  Apple) se suma al clúster como miembro de Incus, nodo de Kubernetes y nodo de Ollama. Se conecta por un adaptador de
  red gigabit TP-Link; si se corta el cable, el WiFi de respaldo ahora sí toma el control, y el prompt avisa si está
  con cargador o a batería. [Ver en el inventario](hardware/inventory.md#eve-macbook-pro-con-chip-t2).
- **8 nov 2026 · Monitoreo listo para cuatro nodos.** Las alertas de Calico comparan con la cantidad real de nodos en
  vez de un número fijo, las métricas de Incus incluyen a `eve` y se arregló un cruce entre Argo CD y el operador de
  VictoriaMetrics que desincronizaba los logs cada cinco minutos. De paso: Open WebUI 0.13, VictoriaMetrics 0.97 y
  parches de los runners. [Monitoreo y alertas](operacion/monitoreo.md).
- **7 nov 2026 · Herramientas al día.** Los playbooks de Ansible instalan opkssh v0.19.2, Ollama 0.40.15, la versión
  actual de la interfaz web de Incus y kube-vip v1.3.1. [Asistente de IA local](operacion/ia-ollama.md).
- **2 nov 2026 · Docker en los runners de GitHub Actions.** Los runners de ARC (Actions Runner Controller) pueden
  construir imágenes con Docker, y el nuevo scale set `arc-php-84` trae PHP (lenguaje de programación web) 8.4 y
  Composer con caché compartida. [Caché de los runners](operacion/cache-arc.md).
- **1 nov 2026 · Actualizaciones automáticas.** Dependabot revisa las dependencias de Python, GitHub Actions y
  OpenTofu, y abre un PR (pull request) cuando sale una versión nueva.
- **26 oct 2026 · La guía en tres miradas.** En las decisiones importantes puedes leer cómo se hace en casa, qué
  cambiaría en una empresa y cuál es el equivalente en la nube; los pasos se muestran desde la interfaz o desde la
  consola, como prefieras. Además, un [glosario](glosario.md) con todas las siglas.
