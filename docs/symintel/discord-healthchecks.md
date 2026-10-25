# Plataforma symintel — Discord y healthchecks.io

Cómo crear, **a mano y una sola vez**, las credenciales del [monitoreo](../implementacion/fase-4-gitops.md#413-monitoreo-y-alertas-opcional):
los webhooks de Discord donde llegan las alertas y el check de healthchecks.io que avisa si el propio monitoreo cae. Al final
se guardan en 1Password y [`playbook-platform-secrets.yml`](https://github.com/symintel/homelab/blob/main/ansible/playbook-platform-secrets.yml)
las lleva al clúster.

!!! info "Los nombres de los menús están en inglés"
    Esta guía usa los textos tal como aparecen en la interfaz en inglés de Discord y de healthchecks.io (**Server Settings**,
    **Add Check**…). Si usas Discord en español, los menús tienen otro nombre pero el mismo orden. Estas plataformas cambian su
    interfaz de vez en cuando: si algún botón no coincide, busca el equivalente en esa misma pantalla.

## Qué se crea

| Qué | Dónde se crea | Item de 1Password | Lo usa |
|---|---|---|---|
| Un **webhook** por canal de alertas: `critical` y `warnings` | Discord | `discord-webhooks` | Alertmanager publica las alertas |
| La **ping URL** de un check | healthchecks.io | `healthchecks-ping` | Alertmanager le manda un ping cada 5 minutos |
| La contraseña del administrador de Grafana | 1Password | `grafana-admin` | Entrar a Grafana |

Un webhook es una URL con la que cualquiera puede **publicar mensajes** en ese canal; no permite leer nada. La ping URL permite
mandar pings al check. Las dos son secretos: no las pegues en git, en el chat ni en un ticket.

## Parte 1 — Discord

Necesitas ser administrador del servidor (o tener el permiso **Manage Webhooks**) para crear los webhooks.

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

Para revocar un webhook, bórralo con **Delete Webhook** en esa misma pantalla: la URL deja de funcionar al instante.

### 5. Que las críticas te lleguen al móvil

Clic derecho en el canal → **Notification Settings** (o **Mute Channel** → opciones):

| Canal | Ajuste |
|---|---|
| `alertas-criticas` | **All Messages** (te llega al móvil) |
| `alertas-avisos` | **Only @mentions**, o silenciado: se mira cuando quieras |

### 6. Probar el webhook (opcional)

Publica un mensaje de prueba sin dejar la URL en el historial de la terminal (la pide en silencio):

```bash
read -rs HOOK        # pega la URL y pulsa Enter (no se ve)
curl -sS -H 'Content-Type: application/json' -d '{"content":"Prueba del webhook"}' "$HOOK"
unset HOOK
```

Debe aparecer "Prueba del webhook" en el canal; `curl` no imprime nada si todo va bien. Un error `404` significa que el webhook no existe
(URL mal copiada o borrado).

## Parte 2 — healthchecks.io

[healthchecks.io](https://healthchecks.io/) funciona como un **dead man's switch**: espera recibir un ping cada cierto tiempo y, si deja
de llegar, te avisa. Se usa para enterarse de que el monitoreo (o todo el clúster) se cayó, algo que el propio monitoreo no podría
decirte. El plan gratuito basta.

### 1. Crear una cuenta

Regístrate en [healthchecks.io](https://healthchecks.io/) con un correo al que tengas acceso. Se crea un proyecto por defecto.

### 2. Crear el check

En la página **Checks**, pulsa **Add Check** y rellena:

| Campo | Valor | Por qué |
|---|---|---|
| **Name** | `homelab-monitoreo` | Es el nombre que verás en el aviso de Discord |
| **Schedule** | **Simple** | Un ping a intervalos fijos |
| **Period** | `5 minutes` | Alertmanager envía el ping cada 5 minutos |
| **Grace Time** | `10 minutes` | Tolera un ping tardío antes de dar el check por caído |

Con esos valores, el aviso llega unos 15 minutos después de que se corte el ping. Guarda el check.

### 3. Copiar la ping URL

En el check, copia su **ping URL**. Tiene este formato, y el script de 1Password exige que empiece con `https://`:

```text
https://hc-ping.com/<uuid>
```

Pégala en el campo `url` del item `healthchecks-ping` (parte 3). Quien tenga esta URL puede mandar pings y así mantener el check en
verde aunque el monitoreo esté caído: trátala como un secreto.

### 4. Conectar el check con Discord

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
script los busca por nombre. Cómo crear un item con campos propios: [Plataforma symintel — GitHub](github.md#como-crear-un-item-con-campos-propios).

| Item | Campo | Contenido |
|---|---|---|
| `discord-webhooks` | `critical` | Webhook de `alertas-criticas` (parte 1, paso 4) |
| | `warnings` | Webhook de `alertas-avisos` |
| `healthchecks-ping` | `url` | La ping URL del check (parte 2, paso 3) |
| `grafana-admin` | `password` | Una contraseña generada con el generador de 1Password |
| | `username` | *(opcional)* usuario del administrador; por defecto `admin` |

Comprueba que están bien puestos, sin mostrar ningún valor (desde `ansible/`):

```bash
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"  # tu cuenta
../.venv/bin/python scripts/apply_platform_secrets.py --check
```

Debe mostrar `✓` en `discord-webhooks`, `healthchecks-ping` y `grafana-admin`. Si alguna URL de Discord no tiene el formato esperado, lo dice con
`✗`.

## Siguiente

Con los items listos, sigue en [4.13 — Monitoreo y alertas](../implementacion/fase-4-gitops.md#413-monitoreo-y-alertas-opcional) (paso 4: crear los
Secrets en el clúster). Para cambiar un webhook o la ping URL más adelante:
[Rotar credenciales](../operacion/rotar-credenciales.md#monitoreo-webhooks-de-discord-ping-de-healthchecksio-y-grafana).
