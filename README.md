# Kroltin
A Command and Control (C2) service for penetration testing

## Fix VMware Workstation install on Debian
When installing VMware Workstation with the Bundle file I ran into a few issues on Debian 12. These issues were fixed by running the following command to install all modules.
```bash
vmware-modconfig --console --install-all
```