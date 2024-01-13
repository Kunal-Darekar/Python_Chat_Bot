import os
from Database import *
from error import *

d_key = ""
def checkKey():
    while True:
        try:
            d_key = int(input('enter your choice: '))
        except ValueError:
            print('please provide interger value')
        else:
            break




def createRoom():

    while True:
        if (d_key == 1):
            os.chdir("D:\PY_PRO\\rooms")
            dir_list = os.listdir()
            room_name = input("Enter Room Name: ")

            while True:
                try:
                    if (len(room_name) <= 2):
                        raise MyError
                except:
                    print("please provide room name length more than 2 char")
                    break
                else:
                    if (room_name+'.' in dir_list):
                        print("Room allready present.. Enter another room name")
                    else:
                        room_pwd = input("Enter Room Password: ")
                        os.chdir("D:\PY_PRO")
                        f = open('Database.txt', 'a')
                        f.write('\n' + room_name + ':' + room_pwd)
                        f.close()
                        appendData()

            break
        elif (d_key == 2):
            print("You selected : Enter in Existing Room ")
            break
        else:
            print("Enter choice either 1 or 2")
            break
    