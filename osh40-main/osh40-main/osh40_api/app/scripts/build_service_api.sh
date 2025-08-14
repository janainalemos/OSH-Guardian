#!/bin/bash

# Access root dir for start docker build
cd /home/ubuntu/api

# Create container docker
sudo docker-compose up -d

# Copy, and start the script to keep container always is executing
sudo cp /home/ubuntu/api/scritps/osh40-api.service /lib/systemd/system/
sudo systemctl enable osh40-api
sudo systemctl start osh40-api
