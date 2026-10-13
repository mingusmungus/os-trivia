#!/bin/bash

# Create the moderator
groupdel moderator 2>/dev/null
sudo /usr/sbin/useradd -m -s /bin/bash moderator

# Set the appropriate file permissions
sudo cp -r ./* /home/moderator
sudo chown -R moderator:moderator /home/moderator
sudo chmod a+x /home/moderator

# Create socket folder
sudo mkdir /home/moderator/sockets
sudo chown moderator:moderator /home/moderator/sockets
sudo chmod 711 /home/moderator/sockets

# Create data folder and logs
sudo mkdir -p /home/moderator/data
sudo touch /home/moderator/data/scores.log
sudo chown moderator:moderator /home/moderator/data/*
sudo chmod 700 /home/moderator/data/scores.log

# Lock down the question and key bank
sudo chmod 600 /home/moderator/trivia.json
