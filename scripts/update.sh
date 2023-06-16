#! /bin/bash
# Pull latest and rebuild docker container
git pull
sudo docker compose down
sudo docker compose build
sudo docker compose up