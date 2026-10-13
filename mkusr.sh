#!/bin/bash

# Enforce root execution
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run with sudo (e.g., sudo ./mkusr.sh)"
  exit 1
fi

# 1. Find the next available player number
NEXT_NUM=1
while id "player$NEXT_NUM" &>/dev/null; do
    ((NEXT_NUM++))
done

NEW_USER="player$NEXT_NUM"
echo "Assigning username: $NEW_USER"

# 2. Prompt for the password
read -sp "Enter password for $NEW_USER: " PASSWORD

if [ -z "$PASSWORD" ]; then
    echo "Error: Password cannot be empty."
    exit 1
fi

# 3. Create the user account
groupdel "$NEW_USER" 2>/dev/null
/usr/sbin/useradd -c "$NEW_USER" -m -k/dev/null -s /bin/bash "$NEW_USER"

# 4. Set the password
/usr/sbin/chpasswd <<< "$NEW_USER:$PASSWORD"

# 5. Add the moderator to the new player's group
usermod -a -G "$NEW_USER" moderator

# 6. Give the player their own copy of the client files
cp /home/moderator/client.py /home/"$NEW_USER"/
cp /home/moderator/comm.py /home/"$NEW_USER"/

# 7. Make the player the owner of their new files
chown "$NEW_USER":"$NEW_USER" /home/"$NEW_USER"/client.py /home/"$NEW_USER"/comm.py

echo "Success! Account '$NEW_USER' is ready to play."
