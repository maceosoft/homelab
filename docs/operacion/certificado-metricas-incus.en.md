# Incus metrics certificate

How the monitoring tool is given permission to **read** Incus metrics, and what to do if it stops
working. If you only want to know what the certificate is, read the first section.

## What a client certificate is

A **client certificate** is a digital ID card. When a program connects to Incus over HTTPS (encrypted web
connection), Incus asks it to identify itself and the program shows its certificate. If Incus has that ID card
on its trust list, it lets it in; otherwise it closes the door. It is similar to an office key: no matter
who carries it, it only opens the doors it was made for.

Each ID card goes hand in hand with a **private key**, which is what proves the card is yours. The certificate can
be shown without risk (it is the public part); the private key is never shared.

**What it is for here.** Each Incus node publishes the CPU, memory, disk and network usage of its instances at
`https://<nodo>:8443/1.0/metrics`. The monitoring agent (`vmagent`, the one that collects metrics) uses this certificate to
get in and read that page every 60 seconds.

**Why it is read-only.** Incus allows certificates of different types. The `metrics` type can only read
metrics: it cannot create, delete or change instances. So if someone stole the monitoring key, they could see how much
CPU an instance uses, but not manage it. That is why an administrator certificate is not used for this.

**Who issues it.** It is issued by `cert-manager` (the Kubernetes component that creates and renews certificates), signed by
the HomeLab's internal CA (certificate authority), `homelab-ca`. It is declared in Git as a `Certificate` resource named
`incus-metrics` in the `monitoring` namespace
([`incus-certificate.yaml`](https://github.com/maceosoft/gitops/blob/main/monitoring/config/scrapes/incus-certificate.yaml)
in the `gitops` repo). The key pair is stored in the Secret `monitoring/incus-metrics` and **the private key never leaves
the cluster**. Incus does not validate the CA: it only accepts the ID cards that are added by hand to its list, and step 2
takes care of that.

## Procedure

You do it once, or every time the certificate is recreated. Argo CD must have already synced
monitoring, and you need the HomeLab kubeconfig (`~/.kube/homelab-k3s.yaml`).

1. **Check that the certificate is issued.** `READY` must be `True`:

    ```bash
    kubectl -n monitoring get certificate incus-metrics
    ```

2. **Register it in Incus** with the `playbook-incus-metrics.yml` playbook (from the `ansible/` folder of the `homelab` repo).
   It reads only the public part of the Secret and adds it to the Incus trust list with the `metrics` type. If it was
   already there, it does nothing:

    ```bash
    ansible-playbook -i inventory.ini playbook-incus-metrics.yml
    ```

3. **Verify.** On `invincible` there must be a client of type `metrics` named `vmagent`:

    ```bash
    sudo incus config trust list
    ```

    And in Grafana, *Explore*, this query must return one value per node with instances:
    `count by (nodename) (incus_procs_total)`.

## If it fails

| Symptom | Probable cause | What to check |
|---|---|---|
| The playbook says *No se pudo leer monitoring/incus-metrics* | Argo CD has not created the `Certificate` yet, or cert-manager did not issue it | `kubectl -n monitoring describe certificate incus-metrics`; that `homelab-ca` is ready (`kubectl get clusterissuer`) |
| The playbook finishes fine but there are no `incus_*` metrics | The agent does not have the Secret yet, or there is no `metrics` client in Incus | `kubectl -n monitoring get secret incus-metrics` and `sudo incus config trust list` on `invincible` |
| Incus metrics disappeared after recreating the `Certificate` | The Secret has a new certificate that Incus does not know | Run step 2 again. To clean up the old ID card: `sudo incus config trust remove <huella>` |
| A specific node does not show up | Incus on that node does not answer on port 8443 | `curl -k https://<nodo>:8443/` from another machine on the LAN |

To change the certificate, delete the Secret (`kubectl -n monitoring delete secret incus-metrics`): cert-manager issues
a new one, and then steps 2 and 3 are repeated. The other key procedures are in
[Rotate credentials](rotar-credenciales.md).
