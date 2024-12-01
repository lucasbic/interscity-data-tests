#!/bin/bash

cd interscity/interscity-platform/deploy/
VAGRANT_VAGRANTFILE=Vagrantfile-standalone vagrant up
cd ansible/
ansible-playbook setup-swarm.yml -i standalone_vagrant_host
ansible-playbook deploy-swarm-stack.yml -i standalone_vagrant_host

