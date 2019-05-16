#!/bin/bash
# Description: install docker daemon and client
# Version: 0.1
#
# Author: wangtao 479021795@qq.com
# Date: 2015/10/28

set -o xtrace

function update_kernel() {
    apt-get update
    apt-get install linux-image-generic-lts-raring linux-headers-generic-lts-raring

    reboot
}

function add_docker_source() {
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
}

# install apt-transport-https support and Docker registry key
function install_key() {
    sudo apt-get install apt-transport-https ca-certificates curl gnupg-agent software-properties-common -y

    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

    sudo apt-key fingerprint 0EBFCD88

    return 0
}

# update time for every 30 minutes
function set_ntp() {
    crontab -l > /tmp/crontab.bak
    echo '30/* * * * * root /usr/sbin/ntpdate ntp.api.bz' >> /tmp/crontab.bak
    crontab /tmp/crontab.bak
}

# install bridge-utils
function install_brctl() {
    apt-get install bridge-utils
}


if [[ $UID -ne 0 ]]; then
    echo "Not root user. Please run as root."
    exit 0
fi

system_version=$(cat /etc/issue | cut -d " " -f2)
if [[ $system_version < "16.04" ]]; then
    echo "Use Ubuntu 16.04 or newer."
    exit 0
fi

bash ./update_source.sh
install_key
add_docker_source

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io

docker -v

# configure ntp
set_ntp

# install brctl
install_brctl

# Set Docker private registry address
read -p "Input private registry address(192.168.0.1:5000): " registry_address
if [[ -z $registry_address ]]; then
    registry_address="127.0.0.1:5000"
fi
# Add Docker registry mirror to speed up image download
# sed -i "s|.*DOCKER_OPTS=.*|DOCKER_OPTS=\"-H 0.0.0.0:2357 -H unix:///var/run/docker.sock --registry-mirror=http://aad0405c.m.daocloud.io --insecure-registry=${registry_address}\"|g" /etc/default/docker
curl -sSL https://get.daocloud.io/daotools/set_mirror.sh | sh -s http://f1361db2.m.daocloud.io

systemctl restart docker

