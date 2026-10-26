# Cinc/Chef lab

Isolated sandbox (Incus VMs, not LXC —Linux system containers— — Chef manages the full OS state:
sysctl, mounts, kernel modules) to learn Chef/CINC (free distribution of Chef) without risking
production. Tested on both architectures of the cluster.

```bash
incus launch images:ubuntu/24.04 cinc-lab-x86 --vm --target=@x86-nodes -c limits.cpu=2 -c limits.memory=2GiB
incus launch images:ubuntu/24.04 cinc-lab-arm --vm --target=@arm64-nodes -c limits.cpu=2 -c limits.memory=2GiB

incus snapshot create cinc-lab-x86 clean-cinc
# restaurar con: incus snapshot restore <vm> clean-cinc
incus snapshot create cinc-lab-arm clean-cinc
```

Cookbooks in [`cinc-lab/cookbooks/`](https://github.com/maceosoft/homelab/tree/main/cinc-lab/cookbooks).

Also evaluated: installing Cinc/Chef as configuration management for the whole HomeLab
— rejected in favor of **Ansible** (agentless, YAML, gentler learning curve)
+ **OpenTofu** (Incus provider) for 3 nodes. Cinc stays as a learning lab,
not as a production component for now.
