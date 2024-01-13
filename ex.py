# d = {'room': '123\n', 'room1': '82'}
# d1 = {}


# for i, j in d.items():
#     if('\n' in j):
#         d1[i] = j[0:-1]
#     if ('\n' not in j):
#         d1[i] = j
# print(d1)
import os
def chatNow(room_name):
    print("Joined Server: ", room_name)
    os.chdir("D:\PY_PRO\\rooms")
    fr = open(room_name+'.txt', 'r')
    

    print('enter 1 to send msg and 0 to receive msg')
    while True:
        x = input('(1/0): ')

        lines = fr.readlines()
        length = len(lines)

        if(x=='0'):
            if(length != 0):
                print(lines[-1])
                fr.close()
            else:
                print('nothing in chat server')
                fr.close()

        elif(x=='1'):
            fw = open(room_name+'.txt', 'a')
            msg = input('enter msg: ')
            fw.write('\n'+msg)
            print('data appended')
        else:
            pass



    


chatNow('room')
