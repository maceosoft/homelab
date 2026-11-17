# Incus Metrics Certificate

How to give the monitoring tool permission to **read** Incus metrics, and what to do if it stops working. If you only want to know what the certificate is, read the first section.

## What is a Client Certificate

A **client certificate** is a digital ID card. When a program connects to Incus over HTTPS (encrypted web connection), Incus asks it to identify itself and the program shows its certificate. If Incus has that ID card noted in its trust list, it lets it in; if not, it closes the door. It is similar to an office key: it doesn't matter who carries it, it only opens the doors it was made for.

Each ID card goes hand in hand with a **private key**, which is what proves the card is yours. The certificate can be shown without risk (it is the public part); the private key is never shared.

**What it is for here.** Each Incus node publishes CPU, memory, disk, and network usage of its instances at `https://<nodo>:8443/1.0/metrics`. The monitoring agent (`vmagent`, the one that collects metrics) uses this certificate to enter and read that page every 60 seconds.

**Why it is read-only.** Incus allows creating certificates of different types. The type `metrics` can only read metrics: it cannot create, delete, or change instances. Thus, if someone stole the monitoring key, they could see how much CPU an instance uses, but not administer it. That is why an administrator's certificate is not used for this.

**Who issues it.** It is issued by `cert-manager` (the Kubernetes component that creates and renews certificates), signed by the HomeLab's internal CA (Certificate Authority), `homelab-ca`. It is declared in Git as a `Certificate` resource named `incus-metrics` in the `monitoring` namespace
([`incus-certificate.yaml`](https://github.com/maceosoft/gitops/blob/main/addons/monitoring/config/scrapes/incus-certificate.yaml)
in the `gitops` repo). The key pair is stored in the Secret `monitoring/incus-metrics` and **the private key never leaves the cluster**. Incus does not validate the CA: it only accepts the ID cards that are manually noted in its list, and step 2 takes care of that.

## Procedure

It is done once, or every time the certificate is recreated. Argo CD must have already synced the monitoring and you need the HomeLab's kubeconfig (`~/.kube/homelab-k3s.yaml`).

1. **Check that the certificate is issued.** It must appear `READY` in `True`:

    ```bash
    kubectl -n monitoring get certificate incus-metrics
    ```

2. **Register it in Incus** with the playbook `playbook-incus-metrics.yml` (from the `ansible/` folder of the `homelab` repo).
   It reads only the public part of the Secret and notes it in Incus's trust list with the type `metrics`. If it was already noted, it does nothing:

    ```bash
    ansible-playbook -i inventory.ini playbook-incus-metrics.yml
    ```

3. **Verify.** In `invincible` there must be a client of type `metrics` named `vmagent`:

    ```bash
    sudo incus config trust list
    ```

    And this query must return a value for each node with instances: `count by (nodename) (incus_procs_total)`.

    === "🖱️ From the UI"

        In Grafana, *Explore*, run the query.

    === "⌨️ From the console"

        Open a tunnel to VictoriaMetrics and query its API (leave the `port-forward` running in another terminal):

        ```bash
        kubectl -n monitoring port-forward svc/vmsingle-vm-victoria-metrics-k8s-stack 8428:8428
        curl -s http://127.0.0.1:8428/api/v1/query --data-urlencode 'query=count by (nodename) (incus_procs_total)'
        ```

## If It Fails

| Symptom | Probable Cause | What to Check |
|---|---|---|
| Playbook says *Could not read monitoring/incus-metrics* | Argo CD has not yet created the `Certificate`, or cert-manager has not issued it | `kubectl -n monitoring describe certificate incus-metrics`; that `homelab-ca` is ready (`kubectl get clusterissuer`) |
| Playbook finishes OK but no metrics `incus_*` | Agent does not yet have the Secret, or there is no `metrics` client in Incus | `kubectl -n monitoring get secret incus-metrics` and `sudo incus config trust list` in `invincible` |
| Incus metrics disappeared after recreating the `Certificate` | Secret has a new certificate that Incus does not know | Run step 2 again. To clean up the old ID card: `sudo incus config trust remove <huella>` |
| A specific node does not appear | That node's Incus is not responding on port 8443 | `curl -k https://<nodo>:8443/` from another machine on the LAN |

To change the certificate, delete the Secret (`kubectl -n monitoring delete secret incus-metrics`): cert-manager issues
a new one, and then repeat steps 2 and 3. Other key procedures are in
[Rotate Credentials](rotar-credenciales.md).
