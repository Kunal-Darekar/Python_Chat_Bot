# import os
# import time

# filename = "demo.txt"
# last_modified_time = os.path.getmtime(filename)

# while True:
#     x =input("Enter 1 to send a message or any other key to check for new messages: ")
#     if int(x) == 1:
#         message = input("Enter your message: ")
#         with open(filename, "a") as file:
#             file.write(message + "\n")
#     else:
#         current_modified_time = os.path.getmtime(filename)
#         if current_modified_time > last_modified_time:
#             with open(filename, "r") as file:
#                 lines = file.readlines()
#                 new_lines = lines[len(lines)-1:]
#                 for line in new_lines:
#                     print(line.strip())
#             last_modified_time = current_modified_time
#         else:
#             print("No new messages.")
#         time.sleep(1)  # Wait for 1 second before checking again


import os
from Database import *
from error import *

# chat here


def chatNow(room_name):
    print("Joined Server: ", room_name)
    os.chdir("D:\PY_PRO\\rooms")
    lastmodtime = os.path.getmtime(room_name)

    while True:
        if os.path.getmtime(room_name) > lastmodtime:
            print("File has been modified!")
        else:
            with open(room_name, "r") as file:
                print(file.read())

chatNow('demo')