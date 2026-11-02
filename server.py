import time
import json
import random
import sys
import select
from comm import TCPServer

# State definitions
LOBBY = 0
ASK_QUESTION = 1
WAIT_BUZZ = 2
ANSWERING = 3
RESOLUTION = 4
GAME_OVER = 5
STARTING = 6

# Game variables
questions_asked = 0
server = TCPServer()
state = LOBBY
players = {}
score = {}
attempted_players = set()
active_buzzer = None
current_trivia = None
countdown_start = 0

# Writes log to file
def log_event(message):
    try:
        with open('scores.log', 'a') as f:
            f.write(f"{time.strftime('%H:%M:%S')} - {message}\n")
    except Exception as e:
        print(f"[ERROR] Could not write to log: {e}")

# Broadcast, log message, and print to server's terminal
# Useful when we want to do all 3, but that's not always the case
def display_log(message):
    server.broadcast({"msg": message})
    log_event(message)
    print(message)

# Load the trivia bank securely
try:
    with open('trivia.json', 'r') as f:
        question_bank = json.load(f)
        max_questions = len(question_bank)

        # Randomize question bank order
        random.shuffle(question_bank)
except PermissionError:
    print("Fatal: Server must be run as 'moderator' to access trivia.json")
    log_event("Fatal: Server must be run as 'moderator' to access trivia.json")
    exit(1)

print("Server running . . .")
log_event("Server running . . .")

# Server state machine processing begins
while True:
    # Process network events
    messages = server.poll_events(timeout=0.1)
    for conn, msg in messages:
        action = msg.get("action")
        
        if action == "join":
            # Initialize name and score
            players[conn] = msg.get("username")
            score[conn] = 0

            # Broadcast lets users know who joined, also print it locally to MOD terminal
            display_log(f"{players[conn]} joined! (Total: {len(players)})")

            # Automatic start based on player count
            if state == LOBBY and len(players) >= 1:
                state = STARTING
                countdown_start = time.time()
                server.broadcast({"msg": "Minimum players reached! Game starting in 10 seconds..."})
                print("Countdown started. . .")
                
            # Sync late-joiners with the current question
            elif state in [WAIT_BUZZ, ANSWERING] and current_trivia:
                server.send_to(conn, {"msg": "You joined mid-game! Here is the current question:"})
                server.send_to(conn, {"type": "question", "msg": f"Q: {current_trivia['q']}"})
                
                # If someone is already typing their answer, let the new player know
                if state == ANSWERING and active_buzzer:
                    server.send_to(conn, {"msg": f"...waiting for {players[active_buzzer]} to answer."})
       
        elif action == "buzz" and state == WAIT_BUZZ:
            if conn in attempted_players:
                server.send_to(conn, {"msg": "XXXX You already had an attempt! XXXX"})

            else:
                attempted_players.add(conn) # Keep track of player attempts
                state = ANSWERING
                active_buzzer = conn
                display_log(f"{players[conn]} buzzed in!")
                server.send_to(conn, {"msg": "Type your answer now!"})
        
        elif action == "text_input":
            user_text = msg.get("text", "")
            
            # If it's their turn to answer a question
            if state == ANSWERING and conn == active_buzzer:
                print(f"{players[conn]} answered: {user_text}")
                accepted_answers = [ans.lower() for ans in current_trivia['a']]

                # Clean the input
                clean_answer = user_text.strip().lower()
                raw_answer = current_trivia['a']

                if isinstance(raw_answer, str):
                    raw_answer = [raw_answer]

                # Give correct answers a point, wrong answers just loops to WAIT_BUZZ state
                if clean_answer in accepted_answers:
                    score[conn] += 1
                    display_log(f"{players[conn]} got it right! Answer: {current_trivia['a'][0]}")
                    display_log(f"{players[conn]} Score: {score[conn]}")
                    state = RESOLUTION

                else:
                    score[conn] -= 1
                    display_log(f"{players[conn]} guessed wrong! '{user_text}', which is not correct.")

                    if len(attempted_players) >= len(players):
                        display_log("Everyone has used up their attempts! Moving on . . .")
                        state = RESOLUTION

                    else:
                        display_log("Anyone else want to try?")
                        state = WAIT_BUZZ
                        active_buzzer = None
                
            # Otherwise, treat the text as a global chat message
            else:
                display_log(f"[CHAT] {players[conn]}: {user_text}")
        
        # Remove traces of dead socket upon player disconnect
        elif action == "disconnect":
            if conn in players:
                dropped_name = players.pop(conn)
                score.pop(conn, None)
                attempted_players.discard(conn)
                
                display_log(f"{dropped_name} disconnected.")
                
                # Edge case: The active player disconnects before hitting enter
                if state == ANSWERING and conn == active_buzzer:
                    active_buzzer = None
                    server.broadcast({"msg": "Active player disconnected! Anyone else want to try?"})
                    state = WAIT_BUZZ

    # Process Game State (e.g., triggering the next question)
    # Automatic start based on player count
    if state == STARTING:
        if time.time() - countdown_start >= 10:
            # https://www.asciiart.eu/art/5e6e97e0bd18eee0, ASCII art by Harry Mason (Hajoma)
            welcome_msg = r"""
         _nnnn_                      
        dGGGGMMb     ,"""""""""""""".
       @p~qp~~qMb    |  OS Trivia!  |
       M|@||@) M|   _;..............'
       @,----.JM| -'
      JS^\__/  qKL
     dZP        qKRb
    dZP          qKKb
   fZP            SMMb
   HZM            MMMM
   FqM            MMMM
 __| ".        |\dS"qML
 |    `.       | `' \Zq
_)      \.___.,|     .'
\____   )MMMMMM|   .'
     `-'       `--' 


Welcome to OS Trivia!
Rules:
 > Press ENTER to buzz in.
 > One attempt per question.
 > Right: +1 pt | Wrong: -1 pt. Buzz wisely!
 > All lowercase letters/numbers, no spaces.
   (e.g., Q: 'What's your name?' A: 'firstnamelastname123')
"""
            server.broadcast({"msg": welcome_msg})
            state = ASK_QUESTION
    
    if state == ASK_QUESTION:
        if questions_asked >= max_questions:
            state = GAME_OVER
        else:
            attempted_players.clear()                       # After each question, attempts are renewed
            current_trivia = question_bank[questions_asked] # Get next question
            questions_asked += 1
            server.broadcast({"type": "question", "msg": f"Q: {current_trivia['q']}"})
            print(f"Question: {current_trivia['q']}")
            log_event(f"Question: {current_trivia['q']}")
            state = WAIT_BUZZ

    if state == RESOLUTION:
        if questions_asked >= max_questions:
            state = GAME_OVER
        else:
            server.broadcast({"msg": f"Next round in 5 seconds, get ready!"})
            print("Next round in 5 seconds, get ready!")
            time.sleep(5)
            state = ASK_QUESTION

    if state == GAME_OVER:
        print("\nGame Over! Calculating final scores . . .")
        log_event("\nGame Over! Calculating final scores . . .")
        server.broadcast({"msg": "\n Game Over! Calculating final scores . . ."})

        sorted_scores = sorted(score.items(), key=lambda item: item[1], reverse=True)

        for c, player_score in sorted_scores:
            player_name = players[c]
            result_msg = f"{player_name}: {player_score}"
            if player_score == max_questions:
                display_log(f"Wow! A perfect score! A round of applause for {player_name}!")
            else:
                display_log(result_msg)
        
        # Flush the final messages, then sever the connections
        server.broadcast({"msg": "Disconnecting all players. Rejoin to play again!"})
        time.sleep(1) 
        server.disconnect_all()
        
        # Scrub the application state
        players.clear()
        score.clear()
        attempted_players.clear()
        
        # Return to lobby
        print("Server reset. Waiting for new players...")
        state = LOBBY
        questions_asked = 0
        random.shuffle(question_bank)

