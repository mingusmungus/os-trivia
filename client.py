import threading
import time
import sys
from comm import UnixDomainClient

def listen_for_server(client):
    while True:
        messages = client.recv_all()
        for msg in messages:
            print(f"\n[Server]: {msg.get('msg')}")
            print("> ", end="", flush=True) # Redraw prompt
        time.sleep(0.1)

username = input("Enter username: ")
client = UnixDomainClient()
client.send({"action": "join", "username": username})

# Start background thread to print incoming broadcasts
listener = threading.Thread(target=listen_for_server, args=(client,), daemon=True)
listener.start()

# Main thread handles user typing
while True:
    try:
        user_input = input("> ")

        # Players "buzz-in" with the ENTER key
        if user_input.strip() == "":
            client.send({"action": "buzz"})

        # Sends the string text from user
        else:
            client.send({"action": "text_input", "text": user_input})

    # Gracefully exit upon hitting Ctrl+C
    except KeyboardInterrupt:
        print("\nExiting game . . .")
        break
