#!/bin/bash

# Enforce root execution
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run with sudo (e.g., sudo ./uninstall.sh)"
  exit 1
fi

echo "Removing moderator account and all project files..."
# The -r flag is critical: it deletes the user AND wipes their entire /home/ directory.
# This automatically destroys the /home/moderator/sockets, data, and trivia.json files.
pkill -u moderator 2>/dev/null
userdel -r moderator 2>/dev/null
rm -rf /home/moderator
echo "moderator removed"

echo "Removing player accounts..."
# Looping up to 20 just in case your old Werewolves project had more than 8 players.
# The 2>/dev/null silently hides errors if a specific player number doesn't exist.
for i in {1..20}; do
    PLAYER="player$i"
    pkill -u "$PLAYER" 2>/dev/null
    userdel -r "player$i" 2>/dev/null
    rm -rf /home/player$i
    echo "player$i removed"
done

# If you ever created a dedicated group (like in the original Werewolves setup)
groupdel werewolves 2>/dev/null

echo "System completely cleaned."
