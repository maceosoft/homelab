# HomeLab — K8s + Incus

<span class="tag tag-status">En construcción activa</span>

¡Hola! Te doy la bienvenida a mi **HomeLab**. Aquí te cuento, paso a paso, cómo armé una pequeña nube en mi casa
para que tú también aprendas a **montar y operar infraestructura moderna**. Uso cuatro computadores (dos Lenovo
pequeños, una placa Orange Pi y una MacBook Pro de 2019 convertida en servidor) que trabajan juntos como un clúster
de Kubernetes (K8s). Lo que practicas aquí son **los mismos patrones que usan las empresas y las grandes nubes**; lo
único que cambia es la escala.

**No necesitas cuatro equipos como los míos.** Puedes practicar a la escala que tengas: en tu propio computador (por
ejemplo, con kind, que levanta un clúster de Kubernetes dentro de contenedores Docker), en un servidor o una máquina
virtual, o en un clúster administrado en la nube. La guía sigue mi HomeLab y no trae un paso a paso para cada caso,
pero los conceptos son los mismos y casi todo lo que se instala sobre Kubernetes funciona igual. Lo que cambia es
cómo creas el clúster y las piezas atadas al hardware, como Incus, que necesita Linux en el equipo. En la
[Fase 0](implementacion/fase-0-preparacion.md) te cuento qué fases puedes seguir según lo que tengas, y la pestaña
**☁️ En la nube** de [Elige cómo leer la guía](#elige-como-leer-la-guia) te muestra el equivalente de cada pieza en
los grandes proveedores.

- **Qué vas a aprender:** a dividir un computador en varios más pequeños (virtualización con Incus), a hacer que
  varios computadores trabajen como uno solo (Kubernetes), a describir todo en archivos de texto para que el sistema
  se ajuste solo (GitOps), a guardar copias de tus datos en más de un equipo (almacenamiento replicado), a entrar a
  todos los servicios con tu cuenta de GitHub (inicio de sesión único), a ver qué pasa en cada equipo (registros y
  monitoreo) y a tener inteligencia artificial (IA) funcionando en tu propia casa.
- **Cómo lo vas a aprender:** cada paso explica qué se hace, por qué se hace así y cómo comprobar que funcionó. Las
  instalaciones están automatizadas con Ansible, así que puedes repetirlas las veces que necesites.
- **Con qué:** casi todo es software libre y de código abierto, sin licencias que pagar. Las excepciones son pocas:
  1Password, el gestor de contraseñas (de pago) donde guardo los secretos y que vas a usar desde la Fase 0, y Open
  WebUI, gratis pero con licencia propia.
- **Con un tutor gratuito:** junto al título de cada paso de la guía hay un botón **Aprende con IA**. Elige
  *Explícamelo*, *Hazme un quiz* o *Algo me falló*: el botón copia una pregunta con el contexto de ese paso y abre un
  cuaderno de NotebookLM que responde solo con esta documentación. [Cómo se usa](aprende.md).

[Empieza por la Fase 0 →](implementacion/fase-0-preparacion.md){ .md-button .md-button--primary }
[Ya sé lo básico: elige tu ruta](#elige-tu-ruta){ .md-button }

!!! tip "Novedades"

    --8<-- "docs/novedades.md:recientes"

    [Ver todas las novedades](novedades.md)

## ¿Qué es esto?

Te lo explico de dos maneras; elige la que te acomode (y si quieres, lee las dos):

=== "En simple"

    Imagina un edificio pequeño con cuatro pisos. Cada piso es un computador. Un programa llamado **Incus** divide cada
    piso en departamentos (máquinas virtuales y contenedores). Encima trabaja un **gerente**, Kubernetes (en su versión
    ligera, K3s), que decide qué aplicación va en qué departamento y reemplaza a la que falle. Todo lo instalado
    queda escrito en un **plano guardado en Git**; otro programa, Argo CD, compara el edificio con el plano y
    corrige cualquier diferencia. Y cada instalación se hace con listas de tareas automáticas (Ansible), así que
    se puede repetir igual las veces que quieras.

    El edificio también tiene su propio **asistente de inteligencia artificial**, que vive en la casa y no cuesta nada:
    varios computadores ejecutan los modelos, se pueden sumar más cuando quieras, y una única «recepción» reparte
    cada pregunta al que tiene el modelo pedido. Un **archivo central** junta
    los registros (logs) de todos los pisos, y cada viernes el asistente escribe un resumen de la semana. Para entrar a
    cualquier cosa, las personas se identifican con su cuenta de GitHub y los programas, con una llave propia.

=== "En detalle técnico"

    Clúster K3s híbrido (control plane ARM64 —arquitectura ARM de 64 bits—, workers x86_64) sobre un clúster Incus de
    cuatro miembros (quórum con dqlite, cluster groups por arquitectura). Red de pods con Calico (VXLAN —Virtual
    Extensible LAN— entre subredes), `LoadBalancer` con MetalLB en L2 (capa 2) y entrada HTTPS (HTTP seguro) por
    Gateway API (Kong) con TLS (Transport Layer Security) de una CA (autoridad certificadora) propia (cert-manager).
    Almacenamiento con OpenEBS LocalPV y Longhorn. La plataforma se despliega por GitOps: un ApplicationSet de Argo CD
    activa las apps por olas desde el repositorio `maceosoft/gitops`, con secretos en 1Password (nunca en Git) y SSO
    (inicio de sesión único) con Dex y GitHub. Ansible hace el bootstrap de los nodos, OpenTofu gestiona los
    repositorios de GitHub y ARC (Actions Runner Controller) ejecuta los pipelines en el propio clúster. Cluster API
    (con CAPN, Cluster API Provider for Incus) crea clústeres efímeros sobre Incus.

    IA local con Ollama en varios nodos detrás de un router propio (`ollama-router`): cada nodo se anuncia solo al
    router y le avisa cada minuto que sigue disponible y qué modelos tiene; el router manda cada pregunta a un nodo que
    tenga el modelo pedido. Se pueden sumar más equipos como nodos. Open WebUI con Dex y Open Terminal como sandbox de
    ejecución de código. Logs con Vector → VictoriaLogs → Grafana y reportes diario y semanal con IA en Discord
    (`#ia`). Seguridad: personas → Dex, máquinas → token + restricción de red, firewall de host con `nftables`; las
    NetworkPolicy `default-deny` se activan por etapas. La documentación se traduce sola al inglés con el mismo Ollama.

## El HomeLab de un vistazo

Estas son las piezas que vas a ir montando, cada una con su analogía para que no se te pierda el hilo:

| Pieza | En simple | Qué hace técnicamente |
|---|---|---|
| Nodos | Los cuatro «pisos» del edificio | Lenovo M920q, M700, Orange Pi 5 Plus y MacBook Pro 16" 2019 (x86_64 y ARM64) |
| **Incus** | El que divide cada piso en departamentos | Gestiona contenedores y VM en un clúster de cuatro miembros |
| **K3s** | El gerente que reparte el trabajo | Kubernetes ligero: control plane en `deborah`, workers en los otros tres |
| **Calico** | Los pasillos entre departamentos | CNI: da red y direcciones a los pods |
| **MetalLB** | El número de teléfono fijo del edificio | Asigna IP de la LAN a los Services `LoadBalancer` |
| **Gateway (Kong)** | La puerta principal con portero | Recibe el tráfico HTTPS y lo envía a cada aplicación |
| **cert-manager** | La oficina que emite los carnets | Emite certificados TLS con una CA propia del HomeLab |
| **Longhorn y OpenEBS** | Bodegas: una rápida y otra con copia de seguridad | Almacenamiento local y replicado entre nodos |
| **Argo CD (GitOps)** | El inspector que compara el edificio con el plano | Sincroniza el clúster con lo que declara Git |
| **Dex** | El mostrador de identificación | SSO: inicia sesión con GitHub en Argo CD, Grafana, Open WebUI, Incus, K3s y SSH |
| **Ollama + router** | El asistente y su recepción | Modelos de lenguaje locales en varios nodos; un router con token elige el nodo según el modelo |
| **Open WebUI y Open Terminal** | La sala de consulta y el taller | Chat con el asistente (entrada con Dex) y un terminal aislado donde el asistente ejecuta código |
| **Vector, VictoriaLogs y Grafana** | El archivo central y sus pantallas | Junta los logs de nodos y pods, los guarda 30 días y los muestra; reportes con IA en Discord |
| **Firewall de host** | Las cerraduras de cada piso | `nftables` en cada nodo, con reversión automática si algo sale mal al aplicarlo |
| **ARC** | Obreros que construyen y prueban | Runners de GitHub Actions dentro del clúster |
| **CAPN** | Una impresora 3D de clústeres | Cluster API para crear clústeres a partir de un manifiesto |

## Elige tu ruta

Elige según lo que ya sabes:

<div class="card">
  <div class="card-kicker">¿Por dónde empiezo?</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Estoy empezando</div>
      <div class="text-muted">Sigue las fases en orden, sin apuro. Cada una trae un bloque «Aprende esta fase» con analogías, un reto práctico y preguntas de repaso.</div>
      <div class="text-muted"><a href="implementacion/fase-0-preparacion/">Fase 0</a> · <a href="implementacion/fase-1-red/">Fase 1</a> · <a href="implementacion/fase-2-incus/">Fase 2</a> · <a href="implementacion/fase-3-k3s/">Fase 3</a> · <a href="glosario/">Glosario</a></div>
    </div>
    <div class="card-col">
      <div class="card-title">Ya sé Linux y Kubernetes</div>
      <div class="text-muted">Ve directo a las decisiones: el GitOps de la plataforma, la arquitectura y los análisis de trade-offs de cada fase.</div>
      <div class="text-muted"><a href="implementacion/fase-4-gitops/">Fase 4 — GitOps</a> · <a href="architecture/overview/">Arquitectura</a> · <a href="gitops/">Catálogo GitOps</a></div>
    </div>
    <div class="card-col">
      <div class="card-title">Vengo a operar</div>
      <div class="text-muted">Procedimientos de rutina: agregar un nodo (también al clúster de Ollama), rotar credenciales, actualizar K3s y Argo CD, revisar logs.</div>
      <div class="text-muted"><a href="operacion/">Operación</a> · <a href="operacion/ia-ollama/">Asistente de IA</a> · <a href="operacion/logs/">Logs</a> · <a href="security/modelo-de-autenticacion/">Seguridad</a> · <a href="secrets/">Secretos</a></div>
    </div>
  </div>
</div>

## Elige cómo leer la guía

No todo el mundo llega con la misma pregunta, así que en las decisiones importantes vas a encontrar tres pestañas.
Elige aquí la que te sirva y la guía la recordará en todas las páginas:

=== "🏠 En casa"

    La guía tal como yo la armé: cuatro equipos y casi todo software libre, sin licencias que pagar. Ideal para aprender
    haciendo y equivocarte sin miedo. Si practicas en tu computador o en una máquina virtual, también es tu
    pestaña: cambia cómo creas el clúster, no lo que aprendes.

=== "🏢 En la empresa"

    Además de cómo se hace aquí, ves qué gana una empresa con cada patrón y qué cambiaría: alta disponibilidad,
    soporte comercial, cumplimiento y respaldos.

=== "☁️ En la nube"

    Ves el servicio equivalente en Google Cloud, AWS, Azure y Oracle Cloud, y qué ganas y qué pierdes al usarlo en vez
    de montarlo tú. Es la mirada que te sirve si practicas en un clúster administrado de la nube.

Lo mismo pasa en los pasos que se pueden hacer de dos formas: elige **🖱️ Desde la interfaz** o **⌨️ Desde la consola**
una vez y la guía te muestra siempre la que prefieres.

## Aprende con IA, gratis

Aquí no estudias sin ayuda. En cada paso de la guía hay un botón **Aprende con IA**: prepara una pregunta de tutor
con el contexto de esa sección y te lleva a un cuaderno de estudio que **responde solo con esta documentación**, con
cuestionarios y resúmenes en audio. Elige tu nivel, pulsa el botón y pega la pregunta en el chat.

- [**Cómo se usa y qué herramientas gratuitas hay**](aprende.md)
- [Abrir el cuaderno de NotebookLM](https://notebooklm.google/){ data-notebook-link="1" } (necesitas una cuenta de Google)
- Si usas otro asistente: [`llms-full.txt`](https://homelab.maceo.cl/llms-full.txt) trae toda la guía en texto plano.

## Hardware

Uso cuatro equipos distintos entre sí: dos Lenovo pequeños, una placa ARM64 y una MacBook Pro que ahora vive enchufada
como servidor. Así se reparten el trabajo:

| Nodo | Modelo | CPU | RAM (medida) | IP (`br0`) | Rol |
|---|---|---|---|---|---|
| `invincible` | Lenovo M920q | i7-8700T x86_64 | 15.5 GB | 192.168.20.6 | Incus (hoy líder de la base de datos) · K3s worker · Ollama |
| `oliver` | Lenovo M700 | i3-6100T x86_64 | 7.7 GB | 192.168.20.7 | Incus quórum · K3s worker · Ollama |
| `deborah` | Orange Pi 5 Plus | RK3588 ARM64 | 31 GB | 192.168.20.5 | K3s control plane · Incus ARM64 · DNS · Ollama |
| `eve` | MacBook Pro 16" 2019 | i9-9980HK x86_64 | 31 GB | 192.168.20.8 | Incus (reserva de la base de datos) · K3s worker · Ollama |

El detalle medido de cada equipo y cuánta RAM (memoria de trabajo) usa cada pieza están en el
[Inventario de hardware](hardware/inventory.md). Si te interesa cómo una MacBook con chip T2 (coprocesador de
seguridad de Apple) terminó como nodo del clúster, está contado en
[eve: MacBook Pro con chip T2](hardware/inventory.md#eve-macbook-pro-con-chip-t2). Si algún día hiciera falta
cambiar el nodo del control plane, el procedimiento está documentado en
[Mover el control plane](operacion/mover-control-plane.md). Y si quieres sumar más equipos como nodos de Ollama,
aquí tienes la [guía](operacion/agregar-nodo-ollama.md).

> Los nombres de los nodos vienen de la serie *Invincible* — ver
> [personajes](https://invincible.fandom.com/es/wiki/Categor%C3%ADa:Personajes).

## Para profundizar

Cuando quieras ir más allá de una fase puntual:

**Guía principal — implementación paso a paso:**

- **[Implementación — visión general](implementacion/index.md)** — las fases 0 a 6 en orden y un mapa de las
  decisiones que tomas en cada una.
- **[Stack tecnológico](implementacion/stack-tecnologico.md)** — un diagrama por capas con cada producto que se usa.

Arquitectura y temas de fondo:

- [Arquitectura (modelo C4, de lo general a lo detallado)](architecture/overview.md) · [Componentes](architecture/nivel-3-componentes.md) · [Despliegue](architecture/nivel-4-despliegue.md)
- [Inventario de hardware](hardware/inventory.md)
- [Catálogo GitOps](gitops/index.md) · [Almacenamiento](storage/index.md) · [Secretos](secrets/index.md)
- [Asistente de IA local](operacion/ia-ollama.md) · [Logs y reportes con IA](operacion/logs.md) · [Modelo de autenticación](security/modelo-de-autenticacion.md)
- [Lab Cinc/Chef](labs/cinc/index.md)

!!! note "Repositorio"
    El código de Ansible, OpenTofu y el agente de nodo de Ollama vive en este
    mismo repo (`maceosoft/homelab`), fuera de `docs/`; los manifiestos de
    Kubernetes, en [`maceosoft/gitops`](https://github.com/maceosoft/gitops).
    Este sitio explica el porqué; el código que realmente se ejecuta está en
    los repositorios. El español es el original: la versión en inglés la
    traduce automáticamente el Ollama del HomeLab.
