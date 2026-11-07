# t2_mac

Drivers de las Mac Intel con chip T2 en Debian (grupo `t2_macs`; hoy: `eve`, MacBookPro16,1).
Fuente: [wiki.t2linux.org](https://wiki.t2linux.org/) y el repo apt
[AdityaGarg8/t2-ubuntu-repo](https://github.com/AdityaGarg8/t2-ubuntu-repo).

## Playbook

[`playbook-t2-mac.yml`](../../playbook-t2-mac.yml).

## Antes: python3 y sudo (`bootstrap/setup_sudo.yml`)

Si al instalar Debian se le pone contraseña a root, queda sin `sudo`, y root no puede entrar por SSH con contraseña.
Por eso `setup_sudo.yml` se corre entrando con tu usuario y subiendo a root con `su`. Antes hay que agregar la IP
de la Mac a `bootstrap/inventory.ini`. Desde `ansible/`:

```bash
ansible-playbook -i bootstrap/inventory.ini bootstrap/setup_sudo.yml --limit <ip> \
  -e ansible_user=<usuario> -b --become-method=su --ask-become-pass   # pide la contraseña de root
```

Si `sudo` ya funciona sin contraseña, alcanza con `-b` en lugar de `-b --become-method=su --ask-become-pass`.

## Qué hace

El hostname no lo toca: se pone a mano (`hostnamectl set-hostname` y `/etc/hosts`).

1. Fuente de consola grande (`t2_mac_console_fontface`/`t2_mac_console_fontsize`, TerminusBold 16x32) para la
   pantalla Retina. Tapa cerrada sin efecto (logind) y `sleep`/`suspend`/`hibernate`/`hybrid-sleep` enmascarados: en T2 la
   suspensión funciona a medias. Además, para que se comporte como servidor:
   - arranca en `multi-user.target` (sin modo gráfico);
   - limita la carga de la batería a `t2_mac_battery_charge_limit` (80 %) con una regla udev, porque vive enchufada;
   - instala y arranca `thermald` (control térmico de Intel);
   - apaga Bluetooth (`t2_mac_disable_bluetooth`);
   - trackpad en la consola con `gpm` (`t2_mac_console_mouse`): mueve el cursor y arrastrar con el clic selecciona
     texto. **No puede pegar**: el trackpad solo le entrega al kernel el botón izquierdo (el clic derecho con dos dedos
     lo arma `libinput` en un escritorio, y en la consola no está). Para pegar, un mouse USB con rueda (clic central).
     La velocidad es `t2_mac_gpm_append` (`-a 6 -d 2`, ajustada a mano en
     `eve`); `-d 1` hace que `gpm` no arranque;
   - apaga la pantalla al cerrar la tapa y la enciende al abrirla: `acpid` llama a `/etc/acpi/t2-mac-lid.sh`, que
     guarda el brillo de `t2_mac_lid_backlight` y lo pone en 0. La Touch Bar no necesita esto: `tiny-dfr` ya la apaga
     al cerrar la tapa y después de un minuto sin uso.

   La hora (NTP) no está aquí: la configura `playbook-hardening.yml` (`systemd-timesyncd`).
2. Repos apt T2 (común y de la versión de Debian) en formato deb822, firmados.
3. Paquetes (`t2_mac_packages`): `linux-t2`, `apple-firmware-script`, `apple-t2-audio-config`, `t2fanrd`, `tiny-dfr`.
   No instala `apple-bce`, `applesmc-t2` ni los `*-dkms`: vienen dentro de `linux-t2` y chocan con él.
4. Parámetros de arranque (`t2_mac_kernel_params`) en `/etc/default/grub.d/t2.cfg`, incluido
   `apple_gmux.force_igd=1` (GPU Intel como principal) y `consoleblank=300` (la pantalla se apaga tras 5 minutos
   sin teclado, también con la tapa cerrada; una tecla la enciende). Se aplican en el siguiente reinicio.
5. Si el nodo no corre el kernel T2: pausa, reinicio y comprobación de que arrancó `*-t2` y de que aparece
   `Apple Internal Keyboard`. El driver del T2 se carga solo por udev; no hace falta `modules-load.d`.
   El kernel de Debian queda en GRUB como respaldo.
6. Apaga la GPU AMD en cada arranque con el servicio `t2-mac-dgpu-off` (`t2_mac_dgpu_off`), usando
   `vga_switcheroo`. Probado en `eve`: el consumo baja de 15 a 12 W y la temperatura unos 4 °C. La wiki de t2linux
   se contradice sobre si funciona en todos los modelos: en otra Mac, pruébalo a mano primero
   (`echo OFF | sudo tee /sys/kernel/debug/vgaswitcheroo/switch`).
7. Arranca `t2fanrd` (ventiladores; necesita el kernel T2).
8. Touch Bar: instala las librerías que `tiny-dfr` necesita y su paquete no declara (`t2_mac_tinydfr_libs`). Además
   instala el servicio `t2-mac-touchbar-fix`: al arrancar, el driver de la pantalla (`appletbdrm`) a veces falla con
   `-110` ("Failed to get display information") y la barra queda negra. El servicio lo detecta y reinicia la
   configuración USB de la Touch Bar (0 y después 2), que es el workaround del mantenedor
   ([t2linux/wiki#635](https://github.com/t2linux/wiki/issues/635), [#729](https://github.com/t2linux/wiki/issues/729)).
   Después arranca `tiny-dfr`.
9. Firmware WiFi: si no está, avisa y termina ahí (ver abajo). Si está, recarga `brcmfmac` cuando falta la
   interfaz `wl*` y comprueba que aparezca.

## Firmware WiFi (paso manual)

El firmware de Broadcom de Apple (BCM4364 en la MacBookPro16,1) solo viene con macOS. Si macOS ya no está en el
disco, el script `get-apple-firmware` (paquete `apple-firmware-script`) lo saca de una imagen de recuperación que
baja de Apple. Hace falta internet; el script descarga la imagen y la borra al terminar.

1. Corre el script. Es interactivo, por eso el `-t`:

   ```bash
   ssh -t amaceo@<ip> sudo get-apple-firmware
   ```

2. Elige **"Download a macOS Recovery Image from Apple and extract the firmware from there"**.
3. Cuando te pida la versión de macOS, elige **Sonoma**. El propio script avisa: *"In order to get complete firmware
   files, download macOS Monterey, Ventura or Sonoma"*. Sequoia y Tahoe no están en esa lista: pueden dejar
   archivos incompletos o terminar con *"Couldn't extract firmware"*. Si pasa eso, se repite el paso con Sonoma.
   Que la Mac sea compatible con Tahoe no importa: el script solo saca los archivos de firmware, no instala
   macOS.
4. El script deja el firmware en `/lib/firmware/brcm` y vuelve a cargar el driver. Comprueba con:

   ```bash
   ssh amaceo@<ip> 'ls /lib/firmware/brcm | grep 4364; ip -br link | grep wl'
   ```

5. Corre otra vez `playbook-t2-mac.yml`: comprueba que aparezca la interfaz `wl*` y, si falta, recarga `brcmfmac`.

### Alternativa: sacar el firmware de otra Mac

Si la descarga desde Apple se traba (con `eve` quedó en 8 KB/s), otra Mac con macOS sirve, incluso una con Apple
Silicon: en `/usr/share/firmware/wifi/C-4364__s-B2` y `C-4364__s-B3` trae los archivos del BCM4364. Con `eve` se hizo
así, con el firmware de macOS 27.2, y el chip cargó bien (`BCM4364/4`, interfaz `wlp5s0`):

1. En la otra Mac, baja el script `https://wiki.t2linux.org/tools/firmware.sh` y corre
   `bash firmware.sh rename_only /usr/share/firmware ~/Downloads/firmware-apple.tar`. Solo lee esa carpeta y arma
   el tar con los nombres que espera Linux. No necesita `sudo`.
2. Copia el tar al nodo y extráelo:
   `scp ~/Downloads/firmware-apple.tar <ip>:/tmp/ && ssh <ip> 'sudo tar -xC /lib/firmware/brcm -f /tmp/firmware-apple.tar'`.
3. Corre otra vez `playbook-t2-mac.yml`, que recarga `brcmfmac` si hace falta.

## No soportado

- **Touch ID:** `t2-touchid` solo usa huellas registradas desde macOS. Sin macOS no hay cómo registrarlas.

## Verificar

```bash
ansible eve -m command -a "uname -r"
ansible eve -m shell -a "grep -E '^N:' /proc/bus/input/devices"
ansible eve -m command -a "systemctl is-active t2fanrd"
ansible eve -m command -a "ip -br link"
```
