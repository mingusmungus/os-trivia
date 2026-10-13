import time
import json
import random
import sys
import select
from comm import UnixDomainServer

# State definitions
LOBBY = 0
ASK_QUESTION = 1
WAIT_BUZZ = 2
ANSWERING = 3
RESOLUTION = 4
GAME_OVER = 5

# Game variables
questions_asked = 0
server = UnixDomainServer()
state = LOBBY
players = {}
score = {}
attempted_players = set()
active_buzzer = None
current_trivia = None

# Writes log to file
def log_event(message):
    try:
        with open('/home/moderator/data/scores.log', 'a') as f:
            f.write(f"{time.strftime('%H:%M:%S')} - {message}\n")
    except Exception as e:
        print(f"[ERROR] Could not write to log: {e}")

# Load the trivia bank securely
try:
    with open('/home/moderator/trivia.json', 'r') as f:
        question_bank = json.load(f)
        max_questions = len(question_bank)

        # Randomize question bank order
        random.shuffle(question_bank)
except PermissionError:
    print("Fatal: Server must be run as 'moderator' to access trivia.json")
    log_event("Fatal: Server must be run as 'moderator' to access trivia.json")
    exit(1)

print("Server running . . .")
print("Messaging players . . .")
print("**** Press ENTER to begin ****")
log_event("Server running . . .")

# Server state machine processing begins
while True:
    if state == LOBBY:
        # Checking if the moderator presses enter
        readable, _, _ = select.select([sys.stdin], [], [], 0.0)

        if readable:
            sys.stdin.readline()

            if len(players) > 0:
                welcome_msg = r"""
   .=======================.
   |  ____   _____         |
   | / __ \ / ____| TRIVIA |
   | |  | | \___ \         |
   | |__| | ____) |        |
   | \____/|_____/         |
   |                       |
   '======================='
   _[_____________________]_

Welcome to OS Trivia!
Rules:
 > Press ENTER to buzz in.
 > One attempt per question.
 > Right: +1 pt | Wrong: -1 pt. Buzz wisely!
 > All lowercase letters/numbers, no spaces.
   (e.g., Q: 'What's your name?' A: 'firstnamelastname123')
"""
                server.broadcast({"msg": welcome_msg})
                print("Game start!")
                log_event("Game start!")
                state = ASK_QUESTION

            else:
                print("Can't start without any players!\n")
                print("**** Press ENTER to begin ****")

    # Process network events
    messages = server.poll_events(timeout=0.1)
    for conn, msg in messages:
        action = msg.get("action")
        
        if action == "join":
            # Initialize name and score
            players[conn] = msg.get("username")
            score[conn] = 0

            # Broadcast lets users know who joined, also print it locally to MOD terminal
            server.broadcast({"msg": f"{players[conn]} joined! (Total: {len(players)})"})
            print(f"{players[conn]} joined! (Total: {len(players)})")
            log_event(f"{players[conn]} joined! (Total: {len(players)})")

            # Automatic start based on player count
            # if state == LOBBY and len(players) >= 3:
                # print("Starting game. . .")
                # state = ASK_QUESTION
       
        elif action == "buzz" and state == WAIT_BUZZ:
            if conn in attempted_players:
                server.send_to(conn, {"msg": "XXXX You already had an attempt! XXXX"})

            else:
                attempted_players.add(conn) # Keep track of player attempts
                state = ANSWERING
                active_buzzer = conn
                server.broadcast({"msg": f"{players[conn]} buzzed in!"})
                print(f"{players[conn]} buzzed in!")
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
                    server.broadcast({"msg": f"{players[conn]} got it right! Answer: {current_trivia['a'][0]}"})
                    server.broadcast({"msg": f"{players[conn]} Score: {score[conn]}"})
                    log_event(f"{players[conn]} got it right! Answer: {current_trivia['a'][0]}")
                    log_event(f"{players[conn]} Score: {score[conn]}")
                    print(f"{players[conn]} got it right! Answer: {current_trivia['a'][0]}")
                    print(f"{players[conn]} Score: {score[conn]}")
                    state = RESOLUTION

                else:
                    score[conn] -= 1
                    server.broadcast({"msg": f"{players[conn]} guessed wrong! '{user_text}', which is not correct."})
                    log_event(f"{players[conn]} guessed wrong! '{user_text}', which is not correct.")

                    if len(attempted_players) >= len(players):
                        server.broadcast({"msg": "Everyone has used up their attempts! Moving on . . ."})
                        log_event("Everyone has used up their attempts! Moving on . . .")
                        print("Everyone has used up their attempts! Moving on . . .")
                        state = RESOLUTION

                    else:
                        server.broadcast({"msg": "Anyone else want to try?"})
                        print("Anyone else want to try?")
                        state = WAIT_BUZZ
                        active_buzzer = None
                
            # Otherwise, treat the text as a global chat message
            else:
                print(f"[CHAT] {players[conn]}: {user_text}")
                server.broadcast({"msg": f"[{players[conn]}]: {user_text}"})
                log_event(f"[CHAT] {players[conn]}: {user_text}")

    # Process Game State (e.g., triggering the next question)
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
                server.broadcast({"msg": f"Wow! A perfect score! A round of applause for {player_name}!"})
                log_event(f"Wow! A perfect score! A round of applause for {player_name}!")
                print(f"Wow! A perfect score! A round of applause for {player_name}!")
            else:
                print(f"{result_msg}")
                log_event(result_msg)
                server.broadcast({"msg": result_msg})
        
        print("Shutting down server . . .")
        log_event("Server shut down success")
        break

