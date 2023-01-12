import json
 
# Opening JSON file
with open('network.json', 'r') as openfile:
 
    # Reading from json file
    net = json.load(openfile)

asList = []

def createRouters(asName):
    listR = [] #list of routers in the AS
    listC = [] #list of the commands for each router in the AS
    asMat = net[asName]['inMatrix']
    asNb = str(net[asName]['asNumber']) 
    asProt = net[asName]['protocol']

    for i in range (0, len(net[asName]['inMatrix'])):
        routerName = asNb + str(i)
        routerNb ='0.0.' + asNb + '.' + str(i)
        ipAdress = ''

        ## add loopback


        ######## add router and command to lists
        if(asProt == 'RIP'):
            text = 'ipv6 router rip' + routerName
        elif(asProt == 'OSPF'):
            text = 'ipv6 router ospf 1\nrouter-id' + routerNb
        listR.append([routerNb, routerName]) #add router number and name to the list of routers
        listC.append("configure terminal\nipv6 unicast-routing\n" + text) #add command to list
       
        ######## declare each interfaces
        for j in range(0, len(net[asName]['inMatrix'])):
            if asMat[i][j] != 0:
                asMat[i][j].append("adresse IP")

    print(asMat)
    print("liste router\n")
    print(listC)
    asList.append([listR,listC])
    return listR, listC



for key in net: #for each AS
    createRouters(key)[0]

# print("\n Liste des AS \n")
# print(asList)

