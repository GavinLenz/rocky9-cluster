## RESOURCES.md

### 1. Provisioning / Automation

- **Ansible Tips & Tricks** – <https://docs.ansible.com/projects/ansible/latest/tips_tricks/index.html>.
  Reminds me what the engine can actually do before I reinvent another shell loop.
- **community.general Collection Docs** – <https://docs.ansible.com/projects/ansible/latest/collections/community/general/index.html>.
  Required reading for modules like `community.general.pam_limits` and `authorized_key`.

### 2. PXE & Kickstart

- **Red Hat Kickstart Reference** – <https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/performing_an_advanced_rhel_installation/kickstart-commands-and-options-reference>.
  The law for `network`, `user`, and `%post` semantics.
- **iPXE Docs** – <https://ipxe.org/scripting> for templating boot menus.

### 3. Scheduler / Validation

- **LANL Pavilion2** – Repo: <https://github.com/lanl/Pavilion>; Docs: <https://pavilion2.readthedocs.io>.
  Critical for the validation role and suite layout.

### 4. Misc

- **Rocky Linux Docs** – <https://docs.rockylinux.org/>. Shared base for Kickstart +
  package expectations.