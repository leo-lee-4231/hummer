#!/bin/bash
# Description: create a private registry
# Version: 0.1
#
# Author: wangtao 479021795@qq.com
# Date: 2015/10/29

set -o xtrace

if [[ $UID -ne 0 ]]; then
    echo "Not root user. Please run as root."
    exit 0
fi

bash ./update_source.sh

# Install Docker if not
docker -v
if [[ $? -ne 0 ]]; then
    echo "Install Docker..."
    bash ./docker_install.sh
fi

if [[ $? -ne 0 ]]; then
        exit 0
fi

REGISTRY_VERSION=2.2

# Download registry image v2.2
docker pull registry:${REGISTRY_VERSION}

# Start registry container
mkdir /opt/registry
docker run -d -p 5000:5000 --restart=always -v /opt/registry:/var/lib/registry --name hummer_registry registry:${REGISTRY_VERSION}

