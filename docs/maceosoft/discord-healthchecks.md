# Plataforma maceosoft — Discord y healthchecks.io

Cómo crear, **a mano y una sola vez**, las credenciales del [monitoreo](../implementacion/fase-4-gitops.md#413-monitoreo-y-alertas-opcional):
los webhooks de Discord donde llegan las alertas y el check de healthchecks.io que avisa si el propio monitoreo cae. Al final
se guardan en 1Password y [`playbook-platform-secrets.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-platform-secrets.yml)
las lleva al clúster.

!!! info "Los nombres de los menús están en inglés"
    Esta guía usa los textos tal como aparecen en la interfaz en inglés de Discord y de healthchecks.io (**Server Settings**,
    **Add Check**…). Si usas Discord en español, los menús tienen otro nombre pero el mismo orden. Estas plataformas cambian su
    interfaz de vez en cuando: si algún botón no coincide, busca el equivalente en esa misma pantalla.

## Qué se crea

| Qué | Dónde se crea | Item de 1Password | Lo usa |
|---|---|---|---|
| Un **webhook** por canal de alertas: `critical` y `warnings` | Discord | `discord-webhooks` | Alertmanager publica las alertas |
| Un tercer **webhook** opcional, `ai`, para el canal `#ia` (reportes diario y semanal con IA) | Discord | `discord-webhooks` | Los reportes publican ahí ([cómo crearlo](../operacion/logs.md#crear-el-canal-ia-y-su-webhook-una-sola-vez)) |
| La **ping URL** de un check | healthchecks.io | `healthchecks-ping` | Alertmanager le manda un ping cada 5 minutos |
| La contraseña del administrador de Grafana | 1Password | `grafana-admin` | Entrar a Grafana |

Un webhook es una URL con la que cualquiera puede **publicar mensajes** en ese canal; no permite leer nada. La ping URL permite
mandar pings al check. Las dos son secretos: no las pegues en Git, en el chat ni en un ticket.

## Parte 1 — Discord

Necesitas ser administrador del servidor (o tener el permiso **Manage Webhooks**) para crear los webhooks.

Esta parte se hace **solo desde Discord** (web o app): crear roles, canales o webhooks por API exige un bot con permisos en
el servidor, y el HomeLab no usa ninguno. Lo único que se puede hacer desde la consola es probar un webhook y borrarlo.

### 1. Un rol para quien ve las alertas

*Server Settings → Roles → Create Role*, con el nombre `devops`. En la pestaña **Members** del rol, añade a las personas que deben
recibir las alertas. Si el rol ya existe, sáltate este paso.

### 2. Una categoría privada

Las alertas incluyen nombres de nodos y de servicios, y tu servidor tiene gente ajena a infraestructura, así que no uses los canales
existentes (`despliegues`, `general`…).

1. Abre el menú del servidor (el nombre, arriba a la izquierda) → **Create Category**.
2. **Category Name:** `🖥️ Infraestructura`. Activa **Private Category** y pulsa **Next**.
3. Elige el rol `devops` (y no `@everyone`) y termina con **Create Category**.

Los canales que crees dentro la heredan: solo `devops` los ve.

### 3. Dos canales

Pasa el ratón sobre la categoría, pulsa el **+** (**Create Channel**), elige **Text** y crea:

| Channel Name | Para qué |
|---|---|
| `alertas-criticas` | 🔴 Algo requiere atención ya (nodo caído, temperatura crítica, volumen sin réplicas) |
| `alertas-avisos` | 🟡 Conviene mirarlo, sin urgencia |

### 4. Un webhook por canal

Repite esto para cada canal:

1. *Server Settings → Integrations → Webhooks → **Create Webhook*** (o **New Webhook** si ya hay alguno). Aparece un webhook nuevo (normalmente
   llamado `Captain Hook`).
2. Ábrelo y cambia:
    - **Name:** `Alertmanager críticas` (o `Alertmanager avisos`).
    - **Channel:** el canal correspondiente (`alertas-criticas` o `alertas-avisos`). Es el dato que decide a dónde llegan los mensajes:
      comprueba que no quedó el canal por defecto.
3. Pulsa **Copy Webhook URL** y pégala directamente en el campo de 1Password (parte 3). **Save Changes**.

La URL tiene este formato, y el script de 1Password rechaza cualquier otro:

```text
https://discord.com/api/webhooks/<id numérico>/<token>
```

Para revocar un webhook:

=== "🖱️ Desde la interfaz"

    Bórralo con **Delete Webhook** en esa misma pantalla: la URL deja de funcionar al instante.

=== "⌨️ Desde la consola"

    La API de Discord deja borrar un webhook con su propia URL, sin bot ni otra credencial. La URL se pega sin eco para que
    no quede en el historial:

    ```bash
    # pega la URL del webhook y Enter (no se ve)
    read -rs HOOK
    curl -fsS -X DELETE "$HOOK"
    unset HOOK
    ```

    `curl` no imprime nada si se borró (Discord responde `204`); un `404` significa que ya no existía.

### 5. Que las críticas te lleguen al móvil

Clic derecho en el canal → **Notification Settings** (o **Mute Channel** → opciones):

| Canal | Ajuste |
|---|---|
| `alertas-criticas` | **All Messages** (te llega al móvil) |
| `alertas-avisos` | **Only @mentions**, o silenciado: se mira cuando quieras |

### 6. Probar el webhook (opcional)

Publica un mensaje de prueba sin dejar la URL en el historial de la terminal (la pide en silencio):

```bash
# pega la URL y pulsa Enter (no se ve)
read -rs HOOK
curl -sS -H 'Content-Type: application/json' -d '{"content":"Prueba del webhook"}' "$HOOK"
unset HOOK
```

Debe aparecer "Prueba del webhook" en el canal; `curl` no imprime nada si todo va bien. Un error `404` significa que el webhook no existe
(URL mal copiada o borrado).

### 7. Un webhook para el canal de despliegues (opcional)

Solo si quieres las [notificaciones de Argo CD](../implementacion/fase-4-gitops.md#414-notificaciones-de-argocd-a-discord-opcional). Aquí se usa
tu canal `despliegues`, que ya existe y **no está en la categoría privada**: lo ve todo el equipo. Es un webhook más, como los del paso 4:

1. *Server Settings → Integrations → Webhooks → **Create Webhook*** (o **New Webhook**).
2. **Name:** `ArgoCD`. **Channel:** `despliegues`.
3. **Copy Webhook URL** y guárdala en el campo `deployments` del item `discord-webhooks` (parte 3).

Las alertas de fallos de sync no necesitan otro webhook: reutilizan el de `alertas-avisos`.

## Parte 2 — healthchecks.io

[healthchecks.io](https://healthchecks.io/) funciona como un **dead man's switch**: espera recibir un ping cada cierto tiempo y, si deja
de llegar, te avisa. Se usa para enterarse de que el monitoreo (o todo el clúster) se cayó, algo que el propio monitoreo no podría
decirte. El plan gratuito basta.

### 1. Crear una cuenta

Regístrate en [healthchecks.io](https://healthchecks.io/) con un correo al que tengas acceso. Se crea un proyecto por defecto.
Esto es **solo desde la web**.

Si vas a crear el check desde la consola (paso 2), en la web entra a los **Settings** del proyecto y crea una **API key** de
lectura y escritura (*read-write*): crearla también es solo desde la web. Es un secreto: no la guardes en un archivo del repo.

### 2. Crear el check

=== "🖱️ Desde la interfaz"

    En la página **Checks**, pulsa **Add Check** y rellena:

    | Campo | Valor | Por qué |
    |---|---|---|
    | **Name** | `homelab-monitoreo` | Es el nombre que verás en el aviso de Discord |
    | **Schedule** | **Simple** | Un ping a intervalos fijos |
    | **Period** | `5 minutes` | Alertmanager envía el ping cada 5 minutos |
    | **Grace Time** | `10 minutes` | Tolera un ping tardío antes de dar el check por caído |

=== "⌨️ Desde la consola"

    La [API de healthchecks.io](https://healthchecks.io/docs/api/) crea el check con los mismos valores, en segundos
    (`timeout` es el *Period* y `grace` el *Grace Time*). La API key del paso 1 se pega sin eco, así no queda en el historial:

    ```bash
    # pega la API key (read-write) y Enter (no se ve)
    read -rs HC_KEY
    curl -fsS -H "X-Api-Key: $HC_KEY" \
      -d '{"name":"homelab-monitoreo","timeout":300,"grace":600}' \
      https://healthchecks.io/api/v3/checks/ | jq -r .ping_url
    unset HC_KEY
    ```

    Imprime la **ping URL** del check nuevo (el campo `ping_url` de la respuesta): es la del paso 3.

Con esos valores, el aviso llega unos 15 minutos después de que se corte el ping. Guarda el check.

### 3. Copiar la ping URL

En el check, copia su **ping URL**. Tiene este formato, y el script de 1Password exige que empiece con `https://`:

```text
https://hc-ping.com/<uuid>
```

Pégala en el campo `url` del item `healthchecks-ping` (parte 3). Quien tenga esta URL puede mandar pings y así mantener el check en
verde aunque el monitoreo esté caído: trátala como un secreto.

### 4. Conectar el check con Discord

Este paso es **solo desde la web**: la integración con Discord se autoriza en el navegador, y la API de healthchecks.io solo
permite listar las integraciones, no crearlas.

1. Arriba, entra a **Integrations** y pulsa **Add Integration**.
2. Elige **Discord** y pulsa **Connect Discord**.
3. Discord te pide autorizar la aplicación de healthchecks.io: elige tu servidor y el canal **`alertas-criticas`**, y autoriza.
4. De vuelta en healthchecks.io, la integración aparece en la lista; pulsa **Test** para que mande un mensaje de prueba a ese canal.
5. En **Checks**, comprueba que la integración de Discord está activada (**ON**) para `homelab-monitoreo`.

!!! note "No es el mismo canal que usa Alertmanager"
    Los avisos de healthchecks.io llegan por su **propia** integración con Discord, no por los webhooks de la parte 1. Así siguen
    funcionando aunque el clúster esté caído, que es justo el caso para el que existe.

### 5. Primer ping

El check aparece como **New** hasta que recibe su primer ping. Si quieres comprobarlo a mano, envía uno (cambia `<ping URL>`):

```bash
read -rs PING; curl -fsS -m 10 --retry 3 "$PING"; unset PING
```

Debe responder `OK` y el check pasa a **Up**. Cuando el monitoreo ya esté desplegado, Alertmanager lo mantiene así cada 5 minutos.

## Parte 3 — Guardarlo en 1Password

Los items van en la bóveda **`HomeLab`**, como **Nota segura**, con los campos **fuera de cualquier sección** y con el nombre exacto, porque el
script los busca por nombre. Cómo crear un item con campos propios: [Plataforma maceosoft — GitHub](github.md#como-crear-un-item-con-campos-propios).

| Item | Campo | Contenido |
|---|---|---|
| `discord-webhooks` | `critical` | Webhook de `alertas-criticas` (parte 1, paso 4) |
| | `warnings` | Webhook de `alertas-avisos` |
| | `deployments` | *(opcional)* Webhook del canal `despliegues`, para las notificaciones de Argo CD (parte 1, paso 7) |
| | `ai` | *(opcional)* Webhook del canal `#ia`, para los reportes con IA ([crearlo](../operacion/logs.md#crear-el-canal-ia-y-su-webhook-una-sola-vez)) |
| `healthchecks-ping` | `url` | La ping URL del check (parte 2, paso 3) |
| `grafana-admin` | `password` | Una contraseña generada con el generador de 1Password |
| | `username` | *(opcional)* usuario del administrador; por defecto `admin` |

=== "🖱️ Desde la interfaz"

    Crea cada item a mano con los campos de la tabla ([cómo](github.md#como-crear-un-item-con-campos-propios)). Para
    `grafana-admin`, genera la contraseña con el generador de 1Password.

=== "⌨️ Desde la consola"

    Con la app de 1Password desbloqueada y la CLI `op` instalado, los tres items se crean con un comando cada uno. Las URL
    son secretas: se leen con `read -rs` (no se ven al pegarlas ni quedan en el historial) y se borran de la variable al terminar.
    Si tienes más de una cuenta de 1Password, exporta antes `OP_ACCOUNT`.

    ```bash
    # pega el webhook de alertas-criticas y Enter
    read -rs DC_CRITICAL
    # pega el webhook de alertas-avisos y Enter
    read -rs DC_WARNINGS
    op item create --category "Secure Note" --vault HomeLab --title discord-webhooks \
      "critical[password]=$DC_CRITICAL" "warnings[password]=$DC_WARNINGS"
    unset DC_CRITICAL DC_WARNINGS

    # Campos opcionales, en el mismo item (despliegues e #ia):
    read -rs DC_DEPLOY; op item edit discord-webhooks "deployments[password]=$DC_DEPLOY"; unset DC_DEPLOY
    read -rs DC_AI;     op item edit discord-webhooks "ai[password]=$DC_AI";                unset DC_AI

    # pega la ping URL de healthchecks.io y Enter
    read -rs HC_URL
    op item create --category "Secure Note" --vault HomeLab --title healthchecks-ping "url[password]=$HC_URL"
    unset HC_URL

    op item create --category "Secure Note" --vault HomeLab --title grafana-admin \
      "password[password]=$(openssl rand -base64 24)" "username[text]=admin"
    ```

    Para ver la contraseña de Grafana cuando la necesites: `op read "op://HomeLab/grafana-admin/password"`. Los nombres del
    item y de los campos son exactamente los que lee `apply_platform_secrets.py`; no los cambies. Los webhooks de Discord se crean
    **solo desde la web** (parte 1); el check de healthchecks.io también se puede crear por API (parte 2, paso 2).

Comprueba que están bien puestos, sin mostrar ningún valor (desde `ansible/`):

```bash
# tu cuenta
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
../.venv/bin/python scripts/apply_platform_secrets.py --check
```

Debe mostrar `✓` en `discord-webhooks`, `healthchecks-ping` y `grafana-admin`. Si alguna URL de Discord no tiene el formato esperado, lo dice con
`✗`.

## Siguiente

Con los items listos, sigue en [4.13 — Monitoreo y alertas](../implementacion/fase-4-gitops.md#413-monitoreo-y-alertas-opcional) (paso 4: crear los
Secrets en el clúster). Para cambiar un webhook o la ping URL más adelante:
[Rotar credenciales](../operacion/rotar-credenciales.md#monitoreo-webhooks-de-discord-ping-de-healthchecksio-y-grafana).
