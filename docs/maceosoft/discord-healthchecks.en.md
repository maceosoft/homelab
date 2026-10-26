# maceosoft Platform — Discord and healthchecks.io

How to create, **by hand and only once**, the credentials for [monitoring](../implementacion/fase-4-gitops.md#413-monitoring-and-alerts-optional): the Discord webhooks where alerts arrive and the healthchecks.io check that warns if the monitoring itself goes down. At the end, they are stored in 1Password and [`playbook-platform-secrets.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-platform-secrets.yml) brings them to the cluster.

!!! info "Menu names are in English"
    This guide uses the text as it appears in the English interface of Discord and healthchecks.io (**Server Settings**, **Add Check**…). If you use Discord in Spanish, the menus have different names but the same order. These platforms change their interface from time to time: if a button does not match, look for the equivalent on the same screen.

## What is Created

| What | Where Created | 1Password Item | Used By |
|---|---|---|---|
| A **webhook** per alert channel: `critical` and `warnings` | Discord | `discord-webhooks` | Alertmanager publishes alerts |
| A third optional **webhook**, `ai`, for the channel `#ia` (daily and weekly reports with AI) | Discord | `discord-webhooks` | Reports publish there ([how to create it](../operacion/logs.md#create-the-ia-channel-and-its-webhook-once)) |
| The **ping URL** of a check | healthchecks.io | `healthchecks-ping` | Alertmanager sends a ping every 5 minutes |
| The Grafana admin password | 1Password | `grafana-admin` | To log into Grafana |

A webhook is a URL that anyone can **post messages** to that channel; it does not allow reading anything. The ping URL allows sending pings to the check. Both are secrets: do not paste them in Git, chat, or a ticket.

## Part 1 — Discord

You need to be an administrator of the server (or have the **Manage Webhooks** permission) to create webhooks.

### 1. A role for those who see alerts

*Server Settings → Roles → Create Role*, with the name `devops`. In the **Members** tab of the role, add the people who should receive alerts. If the role already exists, skip this step.

### 2. A private category

Alerts include node and service names, and your server has people unrelated to infrastructure, so do not use existing channels (`despliegues`, `general`…).

1. Open the server menu (the name, top left) → **Create Category**.
2. **Category Name:** `🖥️ Infraestructura`. Activate **Private Category** and click **Next**.
3. Choose the role `devops` (and not `@everyone`) and finish with **Create Category**.

Channels created within this category inherit: only `devops` can see them.

### 3. Two channels

Hover over the category, click the **+** (**Create Channel**), choose **Text** and create:

| Channel Name | Purpose |
|---|---|
| `alertas-criticas` | 🔴 Something requires immediate attention (node down, critical temperature, volume without replicas) |
| `alertas-avisos` | 🟡 Worth checking, no urgency |

### 4. A webhook per channel

Repeat this for each channel:

1. *Server Settings → Integrations → Webhooks → **Create Webhook*** (or **New Webhook** if one already exists). A new webhook appears (usually named `Captain Hook`).
2. Open it and change:
    - **Name:** `Alertmanager críticas` (or `Alertmanager avisos`).
    - **Channel:** the corresponding channel (`alertas-criticas` or `alertas-avisos`). This determines where messages go: check that the default channel did not remain.
3. Click **Copy Webhook URL** and paste it directly into the 1Password field (part 3). **Save Changes**.

The URL has this format, and the 1Password script rejects any other:

```text
https://discord.com/api/webhooks/<id numérico>/<token>
```

To revoke a webhook, delete it with **Delete Webhook** on the same screen: the URL stops working immediately.

### 5. Receive critical alerts on your mobile

Right-click the channel → **Notification Settings** (or **Mute Channel** → options):

| Channel | Setting |
|---|---|
| `alertas-criticas` | **All Messages** (alerts arrive on your mobile) |
| `alertas-avisos` | **Only @mentions**, or muted: check when you want |

### 6. Test the webhook (optional)

Post a test message without leaving the URL in the terminal history (it is requested silently):

```bash
# pega la URL y pulsa Enter (no se ve)
read -rs HOOK
curl -sS -H 'Content-Type: application/json' -d '{"content":"Prueba del webhook"}' "$HOOK"
unset HOOK
```

It should appear as "Webhook test" in the channel; `curl` does not print anything if everything is fine. An error `404` means the webhook does not exist (URL not copied correctly or deleted).

### 7. A webhook for the deployment channel (optional)

Only if you want [Argo CD notifications](../implementacion/fase-4-gitops.md#414-notificaciones-de-argocd-a-discord-opcional). Here you use your channel `despliegues`, which already exists and **is not in the private category**: it is visible to the whole team. It is another webhook, like those in step 4:

1. *Server Settings → Integrations → Webhooks → **Create Webhook*** (or **New Webhook**).
2. **Name:** `ArgoCD`. **Channel:** `despliegues`.
3. **Copy Webhook URL** and save it in the field `deployments` of the item `discord-webhooks` (part 3).

Deployment failure alerts do not need another webhook: they reuse the one from `alertas-avisos`.

## Part 2 — healthchecks.io

[healthchecks.io](https://healthchecks.io/) works as a **dead man's switch**: it waits to receive a ping at regular intervals and, if it stops receiving, it alerts you. It is used to know if the monitoring (or the entire cluster) has gone down, something the monitoring itself could not tell you. The free plan is sufficient.

### 1. Create an account

Sign up at [healthchecks.io](https://healthchecks.io/) with an email you can access. A default project is created.

### 2. Create the check

On the **Checks** page, click **Add Check** and fill in:

| Field | Value | Why |
|---|---|---|
| **Name** | `homelab-monitoreo` | This is the name you will see in the Discord alert |
| **Schedule** | **Simple** | A ping at fixed intervals |
| **Period** | `5 minutes` | Alertmanager sends the ping every 5 minutes |
| **Grace Time** | `10 minutes` | Tolerates a late ping before marking the check as down |

With these values, the alert arrives about 15 minutes after the ping stops. Save the check.

### 3. Copy the ping URL

In the check, copy its **ping URL**. It has this format, and the 1Password script requires it to start with `https://`:

```text
https://hc-ping.com/<uuid>
```

Paste it into the `url` field of the item `healthchecks-ping` (part 3). Anyone with this URL can send pings and keep the check green even if the monitoring is down: treat it as a secret.

### 4. Connect the check to Discord

1. Above, go to **Integrations** and click **Add Integration**.
2. Choose **Discord** and click **Connect Discord**.
3. Discord will ask you to authorize the healthchecks.io application: choose your server and the channel **`alertas-criticas`**, and authorize.
4. Back in healthchecks.io, the integration appears in the list; click **Test** to send a test message to that channel.
5. In **Checks**, verify that the Discord integration is enabled (**ON**) for `homelab-monitoreo`.

!!! note "It's not the same channel used by Alertmanager"
    Healthchecks.io alerts come through its **own** Discord integration, not through the webhooks from part 1. This ensures they continue to work even if the cluster is down, which is exactly the case for which it exists.

### 5. First ping

The check appears as **New** until it receives its first ping. If you want to test it manually, send one (replace `<ping URL>`):

```bash
read -rs PING; curl -fsS -m 10 --retry 3 "$PING"; unset PING
```

It should respond `OK` and the check changes to **Up**. Once the monitoring is deployed, Alertmanager keeps it up every 5 minutes.

## Part 3 — Save It in 1Password

The items go in the vault **`HomeLab`**, as **Secure Note**, with the fields **outside any section** and with the exact name, because the script looks for them by name. How to create an item with custom fields: [maceosoft Platform — GitHub](github.md#how-to-create-an-item-with-custom-fields).

| Item | Field | Content |
|---|---|---|
| `discord-webhooks` | `critical` | Webhook of `alertas-criticas` (part 1, step 4) |
| | `warnings` | Webhook of `alertas-avisos` |
| | `deployments` | *(optional)* Webhook of the channel `despliegues`, for Argo CD notifications (part 1, step 7) |
| | `ai` | *(optional)* Webhook of the channel `#ia`, for AI reports ([create it](../operacion/logs.md#create-the-ia-channel-and-its-webhook-once)) |
| `healthchecks-ping` | `url` | The ping URL of the check (part 2, step 3) |
| `grafana-admin` | `password` | A password generated with the 1Password generator |
| | `username` | *(optional)* admin user; default `admin` |

??? tip "With the 1Password CLI (`op`)"
    With the 1Password app unlocked and the CLI `op` installed, the three items are created with one command each. The URLs are secrets: they are read with `read -s` (they are not visible when pasted and do not remain in the history) and are deleted from the variable after completion. If you have multiple 1Password accounts, export `OP_ACCOUNT` first.

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

    To view the Grafana password when needed: `op read "op://HomeLab/grafana-admin/password"`. The item and field names are exactly what `apply_platform_secrets.py` reads; do not change them. Discord and healthchecks.io do not have a CLI to create the webhook or the check: that step is **only from the web** (parts 1 and 2).

Verify that they are set correctly, without showing any values (from `ansible/`):

```bash
# tu cuenta
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
../.venv/bin/python scripts/apply_platform_secrets.py --check
```

It should show `✓` in `discord-webhooks`, `healthchecks-ping`, and `grafana-admin`. If any Discord URL does not have the expected format, it will say `✗`.

## Next

With the items ready, proceed to [4.13 — Monitoring and alerts](../implementacion/fase-4-gitops.md#413-monitoring-and-alerts-optional) (step 4: create the Secrets in the cluster). To change a webhook or the ping URL later: [Rotate credentials](../operacion/rotar-credenciales.md#monitoring-discord-webhooks-healthchecksio-ping-and-grafana).
