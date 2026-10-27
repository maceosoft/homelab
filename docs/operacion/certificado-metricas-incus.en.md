# Incus Metrics Certificate

How to give the monitoring tool permission to **read** Incus metrics, and what to do if it stops working. If you just want to know what the certificate is, read the first section.

## What is a Client Certificate

A **client certificate** is a digital ID card. When a program connects to Incus over HTTPS (encrypted web connection), Incus asks it to identify itself and the program shows its certificate. If Incus has that card noted in its list of trusted certificates, it lets it in; if not, it closes the door. It's like an office key: whoever carries it doesn't matter, it only opens the doors it was made for.

Each card comes with a **private key**, which proves that the card is yours. The certificate can be shown without risk (it's the public part); the private key is never shared.

**What it's used for here.** Each Incus node publishes the CPU, memory, disk, and network usage of its instances in `https://<nodo>:8443/1.0/metrics`. The monitoring agent (`vmagent`, the one that collects metrics) uses this certificate to enter and read that page every 60 seconds.

**Why it's read-only.** Incus allows creating certificates of different types. The type `metrics` can only read metrics: it cannot create, delete, or change instances. So, if someone stole the monitoring key, they could see how much CPU an instance uses, but not manage it. That's why an administrator's certificate is not used for this.

**Who issues it.** It is issued by `cert-manager` (the Kubernetes component that creates and renews certificates), signed by the internal HomeLab CA (`homelab-ca`). It is declared in Git as a resource `Certificate` called `incus-metrics` in the namespace `monitoring`
([`incus-certificate.yaml`](https://github.com/maceosoft/gitops/blob/main/monitoring/config/scrapes/incus-certificate.yaml)
in the repo `gitops`). The key pair is stored in the Secret `monitoring/incus-metrics` and **the private key does not leave the cluster**. Incus does not validate the CA: it only accepts the certificates that are manually noted in its list, and that is handled by step 2.

## Procedure

It is done once, or every time the certificate is recreated. It requires that Argo CD has already synchronized the monitoring and that you have the HomeLab kubeconfig (`~/.kube/homelab-k3s.yaml`).

1. **Check that the certificate is issued.** It should appear `READY` in `True`:

    ```bash
    kubectl -n monitoring get certificate incus-metrics
    ```

2. **Register it in Incus** with the playbook `playbook-incus-metrics.yml` (from the folder `ansible/` of the repo `homelab`).
   It reads only the public part of the Secret and notes it in Incus's trusted list with the type `metrics`. If it was already noted, it does nothing:

    ```bash
    ansible-playbook -i inventory.ini playbook-incus-metrics.yml
    ```

3. **Verify.** In `invincible` there should be a client of type `metrics` called `vmagent`:

    ```bash
    sudo incus config trust list
    ```

    And this query should return a value for each node with instances: `count by (nodename) (incus_procs_total)`.

    === "🖱️ From the UI"

        In Grafana, *Explore*, run the query.

    === "⌨️ From the console"

        Open a tunnel to VictoriaMetrics and query its API (leave the `port-forward` running in another terminal):

        ```bash
        kubectl -n monitoring port-forward svc/vmsingle-vm-victoria-metrics-k8s-stack 8428:8428
        curl -s http://127.0.0.1:8428/api/v1/query --data-urlencode 'query=count by (nodename) (incus_procs_total)'
        ```

## If it fails

| Symptom | Likely Cause | What to Check |
|---|---|---|
| The playbook says *Could not read monitoring/incus-metrics* | Argo CD has not yet created the `Certificate`, or cert-manager has not issued it | `kubectl -n monitoring describe certificate incus-metrics`; that `homelab-ca` is ready (`kubectl get clusterissuer`) |
| The playbook completes successfully but there are no metrics `incus_*` | The agent does not yet have the Secret, or there is no client `metrics` in Incus | `kubectl -n monitoring get secret incus-metrics` and `sudo incus config trust list` in `invincible` |
| Incus metrics disappeared after recreating the `Certificate` | The Secret has a new certificate that Incus does not know | Run step 2 again. To clean the old card: `sudo incus config trust remove <huella>` |
| A specific node does not appear | Incus on that node does not respond on port 8443 | `curl -k https://<nodo>:8443/` from another LAN machine |

To change the certificate, delete the Secret (`kubectl -n monitoring delete secret incus-metrics`): cert-manager issues a new one, and then steps 2 and 3 are repeated. Other key rotation procedures are in [Rotate Credentials](rotar-credenciales.md).
