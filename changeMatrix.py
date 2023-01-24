
def addRouter():
    n = len(matrix)
    matrix.append([])
    matrix[n].append([])
    for i in range (0, n):
        matrix[n].append([])
        matrix[i].append([])


def removeRouter(routerNumber):
    n = len(matrix)
    for i in range (0,n):
        matrix[i].pop(routerNumber)
    matrix.pop(routerNumber)

def connectRouter(router1,if1,router2,if2, weight):
    for i in range (0, len(matrix[router1])):
        if matrix[router1][i] != [] :
            if matrix[router1][i][0] == if1:
                print(if1 + "is already attributed towards " + str(i))
                return 0
    for i in range (0, len(matrix[router2])):
        if matrix[router2][i] != [] :
            if matrix[router2][i][0] == if2:
                print(if2 + "is already attributed towards " + str(i))
                return 0
    matrix[router1][router2]=[if1,weight]
    matrix[router2][router1]=[if2,weight]





matrix = [[[],                         ["FastEthernet0/0", 0], ["GigabitEthernet1/0",0], [], [], [], []],
         [["GigabitEthernet1/0",0], [],                       ["GigabitEthernet2/0", 0], ["FastEthernet0/0", 0], [], [], []],
         [["GigabitEthernet1/0",0], ["GigabitEthernet2/0", 0],                       [], [], ["FastEthernet0/0", 0], [], []],
         [[], ["GigabitEthernet2/0",0], [], [], ["GigabitEthernet3/0",0], ["FastEthernet0/0", 0],  ["GigabitEthernet1/0", 10]],
         [[], [], ["GigabitEthernet2/0", 0], ["GigabitEthernet3/0", 0], [], ["GigabitEthernet1/0", 0], ["FastEthernet0/0", 0]],
         [[], [], [], ["GigabitEthernet1/0", 0], ["GigaEthernet2/0", 0], [], []],
         [[], [], [], ["GigabitEthernet2/0", 0], ["GigabitEthernet1/0", 0], [], []]]


connectRouter(0,"FastEthernet0/0", 3, "tata", 0)
print(matrix)