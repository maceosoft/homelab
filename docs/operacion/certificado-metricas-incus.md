# Certificado de métricas de Incus

Cómo se le da a la herramienta de monitoreo permiso para **leer** las métricas de Incus, y qué hacer si deja de
funcionar. Si solo quieres saber qué es el certificado, lee la primera sección.

## Qué es un certificado cliente

Un **certificado cliente** es un carné digital. Cuando un programa se conecta a Incus por HTTPS (cifrado de la
conexión web), Incus le pide que se identifique y el programa le muestra su certificado. Si Incus tiene ese carné
anotado en su lista de confianza, lo deja pasar; si no, cierra la puerta. Es parecido a una llave de oficina: no importa
quién la lleve, abre solo las puertas para las que fue hecha.

Cada carné va de la mano con una **llave privada**, que es lo que demuestra que el carné es tuyo. El certificado se
puede mostrar sin riesgo (es la parte pública); la llave privada no se comparte nunca.

**Para qué sirve aquí.** Cada nodo de Incus publica el uso de CPU, memoria, disco y red de sus instancias en
`https://<nodo>:8443/1.0/metrics`. El agente de monitoreo (`vmagent`, el que recoge las métricas) usa este certificado para
entrar y leer esa página cada 60 segundos.

**Por qué es de solo lectura.** Incus permite crear certificados de distintos tipos. El tipo `metrics` solo puede leer
métricas: no puede crear, borrar ni cambiar instancias. Así, si alguien robara la llave del monitoreo, podría ver cuánta
CPU usa una instancia, pero no administrarla. Por eso no se usa para esto el certificado de un administrador.

**Quién lo emite.** Lo emite `cert-manager` (el componente de Kubernetes que crea y renueva certificados), firmado por
la CA (autoridad certificadora) interna del HomeLab, `homelab-ca`. Se declara en Git como un recurso `Certificate` llamado
`incus-metrics` en el namespace `monitoring`
([`incus-certificate.yaml`](https://github.com/maceosoft/gitops/blob/main/monitoring/config/scrapes/incus-certificate.yaml)
en el repo `gitops`). El par de llaves queda guardado en el Secret `monitoring/incus-metrics` y **la llave privada no sale
del clúster**. Incus no valida la CA: solo acepta los carnés que se anotan a mano en su lista, y de eso se encarga el
paso 2.

## Procedimiento

Se hace una sola vez, o cada vez que el certificado se vuelva a crear. Hace falta que Argo CD ya haya sincronizado el
monitoreo y tener el kubeconfig del HomeLab (`~/.kube/homelab-k3s.yaml`).

1. **Comprueba que el certificado está emitido.** Debe aparecer `READY` en `True`:

    ```bash
    kubectl -n monitoring get certificate incus-metrics
    ```

2. **Regístralo en Incus** con el playbook `playbook-incus-metrics.yml` (desde la carpeta `ansible/` del repo `homelab`).
   Lee solo la parte pública del Secret y la anota en la lista de confianza de Incus con el tipo `metrics`. Si ya
   estaba anotada, no hace nada:

    ```bash
    ansible-playbook -i inventory.ini playbook-incus-metrics.yml
    ```

3. **Verifica.** En `invincible` debe haber un cliente de tipo `metrics` llamado `vmagent`:

    ```bash
    sudo incus config trust list
    ```

    Y en Grafana, *Explore*, esta consulta debe devolver un valor por cada nodo con instancias:
    `count by (nodename) (incus_procs_total)`.

## Si falla

| Síntoma | Causa probable | Qué revisar |
|---|---|---|
| El playbook dice *No se pudo leer monitoring/incus-metrics* | Argo CD aún no creó el `Certificate`, o cert-manager no lo emitió | `kubectl -n monitoring describe certificate incus-metrics`; que `homelab-ca` esté listo (`kubectl get clusterissuer`) |
| El playbook termina bien pero no hay métricas `incus_*` | El agente aún no tiene el Secret, o no hay cliente `metrics` en Incus | `kubectl -n monitoring get secret incus-metrics` y `sudo incus config trust list` en `invincible` |
| Las métricas de Incus desaparecieron tras recrear el `Certificate` | El Secret tiene un certificado nuevo que Incus no conoce | Vuelve a correr el paso 2. Para limpiar el carné viejo: `sudo incus config trust remove <huella>` |
| Un nodo concreto no aparece | Incus de ese nodo no responde en el puerto 8443 | `curl -k https://<nodo>:8443/` desde otro equipo de la LAN |

Para cambiar el certificado, borra el Secret (`kubectl -n monitoring delete secret incus-metrics`): cert-manager emite
uno nuevo, y después se repiten los pasos 2 y 3. Los demás procedimientos de claves están en
[Rotar credenciales](rotar-credenciales.md).
