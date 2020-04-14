#!/bin/bash -Eeu

apk --update add --virtual build-dependencies build-base

pip3 install -r requirements.txt

apk del build-dependencies build-base
rm -vrf /var/cache/apk/*
