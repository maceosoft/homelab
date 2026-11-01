# maceosoft Platform — Discord and healthchecks.io

How to create, **manually and just once**, the credentials for [monitoring](../implementacion/fase-4-gitops.md#413-monitoring-and-alerts-optional):
the Discord webhooks where alerts arrive and the healthchecks.io check that notifies you if monitoring itself goes down. At the end
they are stored in 1Password and [`playbook-platform-secrets.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-platform-secrets.yml)
brings them to the cluster.

!!! info "Menu names are in English"
    This guide uses the texts exactly as they appear in the English UI of Discord and healthchecks.io (**Server Settings**,
    **Add Check**…). If you use Discord in Spanish, the menus have different names but the same order. These platforms change their
    UI from time to time: if a button doesn't match, look for the equivalent on that same screen.

## What gets created

| What | Where created | 1Password item | Used by |
|---|---|---|---|
| One **webhook** per alert channel: `critical` and `warnings` | Discord | `discord-webhooks` | Alertmanager posts alerts |
| A third **optional** webhook, `ai`, for the `#ia` channel (daily and weekly AI reports) | Discord | `discord-webhooks` | Reports publish there ([how to create it](../operacion/logs.md#create-the-ia-channel-and-its-webhook-once)) |
| The **ping URL** of a check | healthchecks.io | `healthchecks-ping` | Alertmanager sends a ping every 5 minutes |
| Grafana admin password | 1Password | `grafana-admin` | Log in to Grafana |

A webhook is a URL that lets anyone **post messages** to that channel; it does not allow reading anything. The ping URL allows
sending pings to the check. Both are secrets: don't paste them in Git, chat, or a ticket.

## Part 1 — Discord

You need to be a server admin (or have the **Manage Webhooks** permission) to create the webhooks.

This part is done **only from Discord** (web or app): creating roles, channels, or webhooks via API requires a bot with permissions in
the server, and the HomeLab doesn't use any. The only thing you can do from the console is test a webhook and delete it.

### 1. A role for who sees alerts

*Server Settings → Roles → Create Role*, named `devops`. In the role's **Members** tab, add the people who should
receive alerts. If the role already exists, skip this step.

### 2. A private category

Alerts include node and service names, and your server has people outside infrastructure, so don't use the existing
channels (`despliegues`, `general`…).

1. Open the server menu (the name, top left) → **Create Category**.
2. **Category Name:** `🖥️ Infraestructura`. Enable **Private Category** and click **Next**.
3. Choose the `devops` role (and not `@everyone`) and finish with **Create Category**.

Channels created inside inherit this: only `devops` can see them.

### 3. Two channels

Hover over the category, click the **+** (**Create Channel**), choose **Text** and create:

| Channel Name | Purpose |
|---|---|
| `alertas-criticas` | 🔴 Something needs attention now (node down, critical temperature, volume without replicas) |
| `alertas-avisos` | 🟡 Worth a look, no rush |

### 4. One webhook per channel

Repeat this for each channel:

1. *Server Settings → Integrations → Webhooks → **Create Webhook*** (or **New Webhook** if there are already some). A new webhook appears (usually
   named `Captain Hook`).
2. Open it and change:
    - **Name:** `Alertmanager críticas` (or `Alertmanager avisos`).
    - **Channel:** the corresponding channel (`alertas-criticas` or `alertas-avisos`). This is the field that decides where messages go:
      verify it didn't stay on the default channel.
3. Click **Copy Webhook URL** and paste it directly into the 1Password field (part 3). **Save Changes**.

The URL has this format, and the 1Password script rejects any other:

```text
https://discord.com/api/webhooks/<id numérico>/<token>
```

To revoke a webhook:

=== "🖱️ From the UI"

    Delete it with **Delete Webhook** on that same screen: the URL stops working instantly.

=== "⌨️ From the console"

    The Discord API lets you delete a webhook with its own URL, no bot or other credential needed. The URL is pasted without echo so
    it doesn't stay in history:

    ```bash
    # pega la URL del webhook y Enter (no se ve)
    read -rs HOOK
    curl -fsS -X DELETE "$HOOK"
    unset HOOK
    ```

    `curl` prints nothing if it was deleted (Discord responds `204`); a `404` means it already didn't exist.

### 5. Get critical alerts on your phone

Right-click the channel → **Notification Settings** (or **Mute Channel** → options):

| Channel | Setting |
|---|---|
| `alertas-criticas` | **All Messages** (reaches your phone) |
| `alertas-avisos` | **Only @mentions**, or muted: check when you want |

### 6. Test the webhook (optional)

Post a test message without leaving the URL in terminal history (it prompts silently):

```bash
# pega la URL y pulsa Enter (no se ve)
read -rs HOOK
curl -sS -H 'Content-Type: application/json' -d '{"content":"Prueba del webhook"}' "$HOOK"
unset HOOK
```

"Prueba del webhook" should appear in the channel; `curl` prints nothing if all goes well. A `404` error means the webhook doesn't exist
(badly copied URL or deleted).

### 7. A webhook for the deployments channel (optional)

Only if you want [Argo CD notifications](../implementacion/fase-4-gitops.md#414-argocd-notifications-to-discord-optional). Here we use
your `despliegues` channel, which already exists and **is not in the private category**: the whole team sees it. It's another webhook, like the ones in step 4:

1. *Server Settings → Integrations → Webhooks → **Create Webhook*** (or **New Webhook**).
2. **Name:** `ArgoCD`. **Channel:** `despliegues`.
3. **Copy Webhook URL** and save it in the `deployments` field of the `discord-webhooks` item (part 3).

Sync failure alerts don't need another webhook: they reuse the `alertas-avisos` one.

## Part 2 — healthchecks.io

[healthchecks.io](https://healthchecks.io/) works as a **dead man's switch**: it expects to receive a ping every so often and, if it stops
arriving, it notifies you. It's used to find out that monitoring (or the whole cluster) went down, something monitoring itself couldn't
tell you. The free plan is enough.

### 1. Create an account

Sign up at [healthchecks.io](https://healthchecks.io/) with an email you have access to. A default project is created.
This is **web-only**.

If you are going to create the check from the console (step 2), in the web UI go to the project **Settings** and create a **read-write API key**: creating it is also web-only. It is a secret: do not store it in a repo file.

### 2. Create the check

=== "🖱️ From the UI"

    On the **Checks** page, click **Add Check** and fill in:

    | Field | Value | Why |
    |---|---|---|
    | **Name** | `homelab-monitoreo` | This is the name you will see in the Discord alert |
    | **Schedule** | **Simple** | A ping at fixed intervals |
    | **Period** | `5 minutes` | Alertmanager sends the ping every 5 minutes |
    | **Grace Time** | `10 minutes` | Tolerates a late ping before marking the check as down |

=== "⌨️ From the console"

    The [healthchecks.io API](https://healthchecks.io/docs/api/) creates the check with the same values, in seconds
    (`timeout` is the *Period* and `grace` the *Grace Time*). The API key from step 1 is pasted without echo, so it does not remain in history:

    ```bash
    # pega la API key (read-write) y Enter (no se ve)
    read -rs HC_KEY
    curl -fsS -H "X-Api-Key: $HC_KEY" \
      -d '{"name":"homelab-monitoreo","timeout":300,"grace":600}' \
      https://healthchecks.io/api/v3/checks/ | jq -r .ping_url
    unset HC_KEY
    ```

    Print the **ping URL** of the new check (the `ping_url` field in the response): this is the one for step 3.

With these values, the alert arrives about 15 minutes after the ping stops. Save the check.

### 3. Copy the ping URL

In the check, copy its **ping URL**. It has this format, and the 1Password script requires it to start with `https://`:

```text
https://hc-ping.com/<uuid>
```

Paste it into the `url` field of the `healthchecks-ping` item (part 3). Anyone with this URL can send pings and keep the check green even if monitoring is down: treat it as a secret.

### 4. Connect the check with Discord

This step is **web-only**: the Discord integration is authorized in the browser, and the healthchecks.io API only allows listing integrations, not creating them.

1. At the top, go to **Integrations** and click **Add Integration**.
2. Choose **Discord** and click **Connect Discord**.
3. Discord asks you to authorize the healthchecks.io application: choose your server and the **`alertas-criticas`** channel, and authorize.
4. Back in healthchecks.io, the integration appears in the list; click **Test** to send a test message to that channel.
5. In **Checks**, verify that the Discord integration is enabled (**ON**) for `homelab-monitoreo`.

!!! note "Not the same channel Alertmanager uses"
    healthchecks.io alerts arrive via its **own** Discord integration, not via the webhooks from part 1. This way they keep working even if the cluster is down, which is exactly the case this exists for.

### 5. First ping

The check shows as **New** until it receives its first ping. If you want to verify it manually, send one (replace `<ping URL>`):

```bash
read -rs PING; curl -fsS -m 10 --retry 3 "$PING"; unset PING
```

It should respond `OK` and the check switches to **Up**. Once monitoring is deployed, Alertmanager keeps it that way every 5 minutes.

## Part 3 — Store in 1Password

Items go in the **`HomeLab`** vault, as a **Secure Note**, with fields **outside any section** and with the exact name, because the script looks them up by name. How to create an item with custom fields: [maceosoft Platform — GitHub](github.md#how-to-create-an-item-with-custom-fields).

| Item | Field | Content |
|---|---|---|
| `discord-webhooks` | `critical` | `alertas-criticas` webhook (part 1, step 4) |
| | `warnings` | `alertas-avisos` webhook |
| | `deployments` | *(optional)* `despliegues` channel webhook, for Argo CD notifications (part 1, step 7) |
| | `ai` | *(optional)* `#ia` channel webhook, for AI reports ([create it](../operacion/logs.md#create-the-ia-channel-and-its-webhook-once)) |
| `healthchecks-ping` | `url` | The check ping URL (part 2, step 3) |
| `grafana-admin` | `password` | A password generated with the 1Password generator |
| | `username` | *(optional)* admin username; defaults to `admin` |

=== "🖱️ From the UI"

    Create each item manually with the fields from the table ([how](github.md#how-to-create-an-item-with-custom-fields)). For
    `grafana-admin`, generate the password with the 1Password generator.

=== "⌨️ From the console"

    With the 1Password app unlocked and the CLI `op` installed, the three items are created with one command each. The URLs
    are secrets: they are read with `read -rs` (not visible when pasted and not kept in history) and cleared from the variable when done.
    If you have more than one 1Password account, export `OP_ACCOUNT` first.

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

    To view the Grafana password when you need it: `op read "op://HomeLab/grafana-admin/password"`. The item and field names are exactly what `apply_platform_secrets.py` reads; do not change them. Discord webhooks are created **web-only** (part 1); the healthchecks.io check can also be created via API (part 2, step 2).

Verify they are set correctly, without showing any values (from `ansible/`):

```bash
# tu cuenta
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
../.venv/bin/python scripts/apply_platform_secrets.py --check
```

It should show `✓` in `discord-webhooks`, `healthchecks-ping` and `grafana-admin`. If any Discord URL does not have the expected format, it reports it with
`✗`.

## Next

With the items ready, continue at [4.13 — Monitoring and alerts](../implementacion/fase-4-gitops.md#413-monitoring-and-alerts-optional) (step 4: create the
Secrets in the cluster). To rotate a webhook or the ping URL later:
[Rotate credentials](../operacion/rotar-credenciales.md#monitoring-discord-webhooks-healthchecksio-ping-and-grafana).
