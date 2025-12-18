# Docker Installation Guide

Bookcard relies on Docker. If you don't have it installed:

- **Windows/Mac**: Install [Docker Desktop](https://docs.docker.com/desktop/).
- **Linux**: Follow the [official installation guide](https://docs.docker.com/engine/install) for your distribution.

## Ubuntu Installation Example

For Ubuntu users, here is a quick reference (see [official docs](https://docs.docker.com/engine/install/ubuntu/) for details):

```bash
# 1. Add Docker's official GPG key:
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update

# 2. Install Docker packages
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 3. Verify installation
sudo docker run hello-world
```

## Linux Post-installation Steps

These optional post-installation procedures describe how to configure your Linux host machine to work better with Docker.

### Manage Docker as a non-root user

The Docker daemon binds to a Unix socket, not a TCP port. By default it's the `root` user that owns the Unix socket, and other users can only access it using `sudo`. The Docker daemon always runs as the `root` user.

If you don't want to preface the `docker` command with `sudo`, create a Unix group called `docker` and add users to it.

> **Warning**: The `docker` group grants root-level privileges to the user. For details on how this impacts security in your system, see [Docker Daemon Attack Surface](https://docs.docker.com/engine/security/#docker-daemon-attack-surface).

To create the `docker` group and add your user:

1.  Create the `docker` group.
    ```bash
    sudo groupadd docker
    ```

2.  Add your user to the `docker` group.
    ```bash
    sudo usermod -aG docker $USER
    ```

3.  Log out and log back in so that your group membership is re-evaluated.
    If you're running Linux in a virtual machine, it may be necessary to restart the virtual machine for changes to take effect.
    You can also run the following command to activate the changes to groups:
    ```bash
    newgrp docker
    ```

4.  Verify that you can run `docker` commands without `sudo`.
    ```bash
    docker run hello-world
    ```

    If you initially ran Docker CLI commands using `sudo` before adding your user to the `docker` group, you may see a permission error. To fix this, change ownership of the `~/.docker/` directory:
    ```bash
    sudo chown "$USER":"$USER" /home/"$USER"/.docker -R
    sudo chmod g+rwx "$HOME/.docker" -R
    ```

### Configure Docker to start on boot with systemd

Many modern Linux distributions use systemd to manage which services start when the system boots. On Debian and Ubuntu, the Docker service starts on boot by default.

To automatically start Docker and containerd on boot for other Linux distributions using systemd, run the following commands:

```bash
sudo systemctl enable docker.service
sudo systemctl enable containerd.service
```

To stop this behavior, use `disable` instead.

```bash
sudo systemctl disable docker.service
sudo systemctl disable containerd.service
```
