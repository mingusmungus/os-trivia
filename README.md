# OS Trivia

### Disclaimer:
Claude was used to write the curses tui in client_tui.py.

### To get the game running:
1. Download the latest release and launch the executable.
2. Enter your username (max 15 characters).
3. Enter the current address:port for the ngrok proxy. If it crashes server-side, a new one will have to be generate, so you'll have to update it if that happens.

### Current ngrok
2.tcp.us-cal-1.ngrok.io:18000

### Game rules:
* Press **BUZZER!** to buzz in when you know the answer.
* One attempt per question.
* Correct Answers: +1 pt.
* You can chat with other players!
* Scroll chat with mouse wheel or PageUP/PageDOWN.
* Press ESC to disconnect.

### Communication Library: 
TCP Sockets, implemented in 'comm.py'. Server is hosted on Google Cloud with ngrok being used to secure the server/client connection.

### Files:
| File            | Usage                                                                       |
|:---------------:|:----------------------------------------------------------------------------|
| server.py       | Hosts the state machine logic and runs the game server.                     |
| client_tui.py   | Lets players communicate with the server for buzzing/chatting/answering.    |
| comm.py         | Implements communication method. Sets up classes for server and client, connects to proper IP and port, continuously polls for I/O with select().|
| trivia.json     | Contains the question/answer bank.                                          |
