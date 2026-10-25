# Lab de Cinc/Chef

Sandbox aislado (VMs Incus, no LXC — Chef gestiona estado de SO completo:
sysctl, mounts, módulos de kernel) para aprender Chef/CINC sin arriesgar
producción. Probado en ambas arquitecturas del clúster.

```bash
incus launch images:ubuntu/24.04 cinc-lab-x86 --vm --target=@x86-nodes -c limits.cpu=2 -c limits.memory=2GiB
incus launch images:ubuntu/24.04 cinc-lab-arm --vm --target=@arm64-nodes -c limits.cpu=2 -c limits.memory=2GiB

incus snapshot create cinc-lab-x86 clean-cinc
incus snapshot create cinc-lab-arm clean-cinc   # restaurar con: incus snapshot restore <vm> clean-cinc
```

Cookbooks en [`cinc-lab/cookbooks/`](https://github.com/maceosoft/homelab/tree/main/cinc-lab/cookbooks).

Evaluado también: instalar Cinc/Chef como config-management del HomeLab
entero — descartado a favor de **Ansible** (agentless, YAML, menor curva)
+ **OpenTofu** (provider de Incus) para 3 nodos. Cinc queda como lab de
aprendizaje, no como pieza de producción por ahora.
