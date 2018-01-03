#!/usr/bin/env python
#-*- coding: utf-8 -*-
# used for docker container discovery in zabbix
# author: zgwldrc
# requirements: 
#   - pip install docker
#   - python 2.7

if __name__ == "__main__":
    import docker
    import json
    client = docker.from_env()
    data = [{"{#CONTAINERNAME}": container.name} for container in client.containers.list()]
    print json.dumps({"data": data}, indent=2)

