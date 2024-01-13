room_deatils = dict()
l2 = []
def appendData():
    f = open('Database.txt', 'r+')


    l = f.readlines()
    for i in l:
        l2.append(i.split(':'))


    room_deatils = dict()
    for i in l2:
        room_deatils.update({i[0]: i[1]})
    
    return(room_deatils)
    
    # print(room_deatils)

# appendData()
