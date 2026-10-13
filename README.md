# OS Trivia

### To get the game running:
1. Run sudo ./install.sh to get the moderator/sockets setup
2. Run sudo ./mkusr.sh for each player in the game
3. Log into moderator and player1, player2, etc. using sudo su - [name]
4. Moderator runs python3 server.py, players run python3 client.py
5. Run sudo ./uninstall.sh when finished

### Game rules:
* Press ENTER to buzz in.
* One attempt per question.
* Right: +1 pt | Wrong: -1 pt. Buzz wisely!
* All lowercase letters/numbers, no spaces.
  *(e.g., Q: 'What's your name?' A: 'firstnamelastname123')

### Communication Library: 
Unix Sockets, implemented in 'comm.py'

### Files:
* server.py: Hosts the state machine logic and runs the game server.
* client.py: Lets players communicate with the server for buzzing/chatting/answering.
* comm.py: Implements communication method. Sets up classes for server and client, creates socket. 
* trivia.json: Contains the question/answer bank, 10 pairs total.
* install.sh: Creates moderator, sockets, and assigns the appropriate permissions.
* mkusr.sh: Sets up a player# account each time it is ran, gives copy of client.py/comm.py files and assigns permission.
* uninstall.sh: Removes all moderator/player accounts.
