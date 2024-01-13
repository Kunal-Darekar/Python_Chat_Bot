import os
from Database import *
from error import *


# chat here

def chatNow(person_name,room_name):
    print("Joined Server: ", room_name)
    os.chdir("D:\PY_PROJECT\\rooms")
    # lastmodtime = os.path.getmtime("D:\PY_PRO\\rooms\\"+room_name+'.txt')

    print("press 1 for send msg and 0 for receive msg\n\n")
    while True:
        x = input('\n\nsend or receive(0/1): ')

        if x == '1':
            message = input("Enter msg: ")
            with open(room_name+'.txt', "a") as f:
                f.write(person_name+': '+ message + "\n")
                print('YOU',':', message)

        elif x == '0':
            with open(room_name+'.txt', "r") as f:
                lines = f.readlines()
                if(len(lines) != 0):
                    new_lines = lines[len(lines)-1:]
                    for line in new_lines:
                        last_msg = line.strip()
                        if(last_msg.startswith(person_name)):
                            print("YOU: ", last_msg,"\n")
                        else:
                            print("OTHER: ", last_msg,"\n")
                else:
                    print('NO SINGLE MSG IN SERVER\n')


        else:
           print('please enter 0 or 1')

 


# login here
class Login:
    def __init__(self, person_name,room_name, room_pwd):
        self.person_name = person_name
        self.room_name = room_name
        self.room_pwd = room_pwd

        d = appendData()
        d1 = {}

        for i, j in d.items():
            if ('\n' in j):
                d1[i] = j[0:-1]
            else:
                d1[i] = j

        for i, j in d1.items():
            if (i == self.room_name and j == self.room_pwd):
                print("Successfully Joined Room 🙂\n")
                chatNow(person_name,room_name)
                break
        else:
            print("Incorrect Password 😑")


while True:
    d = {1: "Create New Room", 2: "Enter in Existing Room"}
    print()
    for i, j in d.items():
        print(i, ".", j, sep='')
    while True:
        try:
            d_key = int(input('Enter your choice(1/2): '))
        except ValueError:
            print('please provide interger value😑')
        else:
            break

    while True:

        # if entered 1
        if (d_key == 1):
            os.chdir("D:\GPA\PY_PROJECT")
            dir_list = os.listdir()
            room_name = input("\nEnter Room Name(creating room): ")

            while True:

                if (len(room_name) <= 2):
                    print("Provide room name more than 2 char")
                    break
                elif (room_name+'.'+'txt' in dir_list):
                    print("Room allready present.. Enter another room name 😑")
                    break
                else:
                    room_pwd = input("Enter Room Password(creating room): ")
                    with open(room_name+'.txt', 'w') as rm:
                        pass
                    os.chdir("D:\GPA\PY_PROJECT")
                    f = open('Database.txt', 'a')
                    f.write('\n' + room_name + ':' + room_pwd)
                    f.close()
                    # appendData()
                    print("\nNow room is created so just join room by entering:")
                    print('Room Name: ', room_name,
                          '& Room Password: ', room_pwd)
                    break
            break

        # if entered 2
        if (d_key == 2):

            os.chdir("D:\GPA\PY_PROJECT\\rooms")
            l = tuple(os.listdir())
            os.chdir("D:\GPA\PY_PROJECT")

            
            person_name = input("\nEnter Your Name👤: ")

            room_name = input("\nEnter Room Name💬: ")
            room_pwd = input("Enter Room Password🔑: ")

            if (room_name+'.txt' in l and len(room_pwd) != 0):
                room = Login(person_name,room_name, room_pwd)
                break

            else:
                print("\nRoom not found. or Wrong Password😑\n")
                break


    # entered value not as 1 or 2
        if(d_key!=1 or d_key!=2):
            print("\nEnter choice either 1 or 2 😑")
            break
  
