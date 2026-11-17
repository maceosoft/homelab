# incus_s3

Publica el **S3 de Incus** (buckets del pool `local`) en `https://192.168.20.6:8555` con un certificado firmado por la
CA del HomeLab (`homelab-ca` de cert-manager), para los respaldos de CloudNativePG.

Incus sirve todos sus listeners (API, clúster, métricas y buckets) con el mismo certificado del clúster y no permite
otro para los buckets. Para no cambiar el certificado de la API, Incus escucha S3 solo en loopback
(`core.storage_buckets_address=127.0.0.1:8556`) y HAProxy (modo `tcp`) termina TLS en `:8555` y vuelve a cifrar hacia
Incus, verificando el certificado del clúster fijado.

## Playbook

[`playbook-incus-s3.yml`](../../playbook-incus-s3.yml), en `invincible` (el miembro que guarda los buckets).

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-incus-s3.yml                           # preflight, no cambia nada
ansible-playbook -i inventory.ini playbook-incus-s3.yml -C --diff                 # qué cambiaría
ansible-playbook -i inventory.ini playbook-incus-s3.yml -e incus_s3_confirm=true  # aplica
```

## Variables

| Variable | Default | Descripción |
|---|---|---|
| `incus_s3_confirm` | `false` | Sin `true` solo hace el preflight |
| `incus_s3_listen_address` / `incus_s3_port` | `static_ip` / `8555` | Endpoint público |
| `incus_s3_backend_address` | `127.0.0.1:8556` | `core.storage_buckets_address` del miembro |
| `incus_s3_tls_sans` | IP del nodo y su nombre | SAN del certificado |
| `incus_s3_tls_duration` | `8760h` | Duración (1 año) |
| `incus_s3_tls_renew_days` | `30` | Renueva si vence antes de esto |
| `incus_s3_tls_force_renew` | `false` | Fuerza un certificado nuevo |

## Qué hace

1. Preflight (solo lectura): lee `ca.crt` de `cert-manager/homelab-ca` (nunca la llave), el valor actual de
   `core.storage_buckets_address`, si existe el bucket `postgres-backups` y el estado del certificado instalado.
2. Instala HAProxy y deja en `/etc/haproxy/incus-s3/` la CA del HomeLab y el certificado público del clúster Incus.
3. Si hace falta, genera llave y CSR en el nodo, crea un `CertificateRequest` para el ClusterIssuer `homelab-ca`, espera
   la firma, borra el pedido, verifica cadena y par de llaves e instala `tls.pem` (el anterior queda como `tls.pem.prev`).
4. Pone `core.storage_buckets_address` en loopback, escribe `haproxy.cfg` (validado con `haproxy -c`) y recarga.
5. Verifica con conexiones nuevas: TLS contra la CA del HomeLab y respuesta S3 (403 sin credenciales).

El puerto 8555 en el firewall lo abre `host_firewall` (servicio `incus-s3`: nodos, pods y operador).

## Documentación

- [PostgreSQL de la plataforma y S3 de Incus](../../../docs/storage/postgres.md)
