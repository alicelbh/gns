import sys
import json
import copy
import time
import telnetlib
import io

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot

def configureInsideProtocols(asName, uB, lAS):
    listR = [] #list of routers in the AS
    listC = [] #list of the commands for each router in the AS

    asMask = "/" +net[asName]['mask']
    asMat = net[asName]['inMatrix']
    asNb = str(net[asName]['asNumber']) 
    asProt = net[asName]['protocol']
    asPrefix = str(net[asName]['prefix'])
    matLen = len(net[asName]['inMatrix'])
    linkNumber = 0

    for i in range (0, matLen): #for each router
        routerName = asNb + str(i+1)
        routerID = asNb + '.0.0.' + str(i+1)
        loopBackAddress = asNb + "::" + str(i+1)
        routerDefinition = {
            "routerName" : routerName,
            "routerID" : routerID,
            "loopBackAddress" : loopBackAddress
        }

        listR.append(routerDefinition) #add router number, name and loopback address to the list of routers. This list of routers will then be added to the global variable "listAS" so that we can access it from outside the function

        borderAsDic = {}
        textBorder = ""

        #configure the interfaces of the border routers in their small subnets
        textBorder+= ipForBorderRouters(borderMat, asNb, asMask, uB, i)

        #configure the interfaces of the rest of the routers
        for j in range(i, matLen): #we only go through half of the matrix since we can get the two routers on a link by getting asMat[i][j] and asMat[j][i] 
            if asMat[i][j] != 0:
                subNetAddress = asPrefix +  asNb + ":" + str(linkNumber) + "::"
                inAddress = asPrefix +  asNb + ":" + str(linkNumber) + "::" + "1"
                inAddressNeighbor = asPrefix +  asNb + ":" + str(linkNumber) + "::" + "2"

                asMatDic = {
                    "interface" : asMat[i][j][0],
                    "@ip" : inAddress,
                    "@subnet" :  subNetAddress,
                    "metric" : asMat[i][j][1]
                }
                asMatDicNeighbor = {
                    "interface" : asMat[j][i][0],
                    "@ip" : inAddressNeighbor,
                    "@subnet": subNetAddress,
                    "metric" : asMat[j][i][1]
                }
            
                # progressively replace the raw adjacency matrix data by a dictionary that'll make easier to find the variables we need (subnet address, interface, ip address, etc) 
                asMat[i][j] = asMatDic
                asMat[j][i] = asMatDicNeighbor
                linkNumber += 1


        #generate the written configurations
        text = "enable\nconfigure terminal\nipv6 unicast-routing\n"
        if(asProt == 'RIP'):
            text += 'ipv6 router rip ' + routerName + "\nexit\n"
            for a in range (0, matLen): #configure all of the physical interfaces
                if asMat[i][a] !=0:
                    text += "interface " + asMat[i][a]["interface"] + "\nipv6 enable" + "\nipv6 address " + asMat[i][a]["@ip"] + asMask + "\nno shutdown\nipv6 rip " + routerName + " enable \nexit\n"
            text+= "interface loopback 0\nipv6 enable\nipv6 address " + loopBackAddress + "/128" + "\nno shutdown\nipv6 rip " + routerName + " enable \nexit\n"
            text+= textBorder
            if borderAsDic != {}:
                text+= ""

        elif(asProt == 'OSPF'):
            text += 'ipv6 router ospf 1\nrouter-id ' + routerID + "\nexit\n"
            for a in range (0, matLen): #configure all of the physical interfaces
                if asMat[i][a] !=0:
                    text+= "interface " + asMat[i][a]["interface"] + "\nipv6 enable" + "\nipv6 address " + asMat[i][a]["@ip"] + asMask + "\nno shutdown\nipv6 ospf 1 area 0\nexit\n"
            text+= "interface loopback 0\nipv6 enable\nipv6 address " + loopBackAddress + "/128" + "\nno shutdown\nipv6 ospf 1 area 0 \nexit\n"
            text+= textBorder

        listC.append(text) #add command to list

    asSpecifications = {
        "routers" : listR,
        "config" : listC,
        "matrix" : asMat
    }

    lAS.append(asSpecifications)

def ipForBorderRouters(borderMat, asNb, asMask, uB, i):
    t = ""
    for b in range (0, len(borderMat)):
                if borderMat[int(asNb)-1][b] != 0: #check if there exist a connection betwteen our AS and another one
                    l = []
                    for z in range (0,len(borderMat[int(asNb)-1][b]), 3): #if there exists one, check if the number of the router i is in the border matrix
                        if borderMat[int(asNb)-1][b][z] == i: 
                            borderAsDic = {
                                "router" : i,
                                "interface" : borderMat[int(asNb)-1][b][z+1],
                                "@ip" : str(borderMat[int(asNb)-1][b][z+2])  + ":" + asNb,
                                "@subnet" :  borderMat[int(asNb)-1][b][z+2] + ":" + asMask
                            }
                            uB[int(asNb)-1][b].append(borderAsDic)
                            t += "interface " + borderAsDic["interface"] + "\nipv6 enable" + "\nipv6 address " + borderAsDic["@ip"] + asMask + "\nno shutdown\nexit\n" 
    return t


def configureBorderProtocol(lAS, uB):
    adjAS = net['adjAS']
    for n in range(0, len(lAS)):
        mask = "/" + str(net['AS' + str((n+1))]['mask'])
        ####### configure iBGP
        for i in range(0, len(lAS[n]["routers"])):
            lAS[n]["config"][i] += "router bgp " + str(n+1) +"\nno bgp default ipv4-unicast\nbgp router-id " + lAS[n]["routers"][i]["routerID"] + "\n"
            for j in range(0, len(lAS[n]["routers"])):
                if i != j:
                    lAS[n]["config"][i] += "neighbor " + lAS[n]["routers"][j]["loopBackAddress"] +" remote-as " +str(n+1)+"\nneighbor " + lAS[n]["routers"][j]["loopBackAddress"] +" update-source Loopback0\n"
            lAS[n]["config"][i] += "address-family ipv6 unicast\n"
            for j in range(0, len(lAS[n]["routers"])):
                if i!=j:
                    lAS[n]["config"][i] += "neighbor " + lAS[n]["routers"][j]["loopBackAddress"] +" activate\n"
            for j in range(0, len(lAS[n]["matrix"][i])):
                if lAS[n]["matrix"][i][j] != 0:
                    lAS[n]["config"][i] += "network " + lAS[n]["matrix"][i][j]["@subnet"] + mask +"\n"
            lAS[n]["config"][i] += "exit\n"
        ####### configure eBGP
        for i in range(0, len(adjAS[n])):
            if (adjAS[n][i]) != 0:
                for y in range(0, len(uB[n][i])):
                    router = uB[i][n][y]['router']
                    address =  uB[i][n][y]['@ip']

                    lAS[n]["config"][router] += "neighbor " + address + " remote-as " + str(i+1) + "\naddress-family ipv6 unicast\nneighbor " + address + " activate\nnetwork " + uB[n][i][y]['@subnet'] + "\nexit\n"

def telnetHandler(lAS):
    for i in range(len(net.keys()) - 1):
        nbRouters = len(net["AS" + str(i+1)]['inMatrix'])
        for j in range(nbRouters): 
            time.sleep(0.1)
            
            port = net["AS" + str(i+1)]["listPorts"][j]
            print(port)
            #tn = telnetlib.Telnet("localhost", port)
            buf = io.StringIO(lAS[i]["config"][j])
            read_lines = buf.readlines()

            for line in read_lines:
                print(line)
                #we write each line in the router's console
                #tn.write(b"\r\n")
                #tn.write(line.encode('utf_8') + b"\r\n")
                #time.sleep(0.1)
    print("Done")

def generateTextFiles(lAS):
    for i in range (0, len(lAS)):
        for r in range (0, len(lAS[i]['config'])):
            f = open("configs/as"+ str(i+1) + "_router" + str(r+1) +".txt", "w")
            f.write(lAS[i]['config'][r])


def button1_clicked(lAS, uB):
   #implement the inner protocols of each AS
    for key in net: #for each 
        if (key!="adjAS"):
            configureInsideProtocols(key, uB, lAS)

    configureBorderProtocol(lAS, uB) #implement the border protocols between all the connectes AS

    generateTextFiles(lAS) #generate writter config
    
    telnetHandler(lAS) #send the config to telnet

def window(lAS, uB):
    app = QApplication(sys.argv)
    widget = QWidget()

    button1 = QPushButton(widget)
    button1.setText("Generate files")
    button1.move(20,32)
    button1.clicked.connect(lambda:button1_clicked(lAS, uB))

    routerConnections = QLineEdit(widget)
    routerConnections.move(20, 160)
    routerConnections.setPlaceholderText("Connections")
    routerConnections.resize(280,40)
    asN = QLineEdit(widget)
    asN.move(20, 100)
    asN.setPlaceholderText("Number of the AS you want to modify")
    asN.resize(280,40)

    b2 = QPushButton(widget)
    b2.setText("Add router")
    b2.move(20, 220)
    b2.clicked.connect(lambda:addRouter(asN, lAS))

    b3 = QPushButton(widget)
    b3.setText("Add connection")
    b3.move(120, 220)
    b3.clicked.connect(lambda:connectRouter(routerConnections, asN, lAS))

    widget.setGeometry(50,50,700,500)
    widget.setWindowTitle("Dudu")
    widget.show()
    sys.exit(app.exec_())

def addRouter(asN, lAS):

    nb = int(asN.text())
    asN.setText("")
    print(nb)
    print(len(lAS))
    n = len(lAS[nb-1]["matrix"])
    lAS[nb-1]["matrix"].append([])
    lAS[nb-1]["matrix"][n].append([])
    for i in range (0, n):
        lAS[nb-1]["matrix"][n].append([])
        lAS[nb-1]["matrix"][i].append([])
    print(lAS[nb-1]["matrix"])



def connectRouter(rCo, nb, lAS):
    connections = rCo.text()
    l = [str(num) for num in connections.split()]

    router1 = l[0]
    if1 = l[1]
    router2 = l[2]
    if2 = l[3]
    weight = l[4]

    rCo.setText("")
    for i in range (0, len(lAS[nb-1]["matrix"][router1])):
        if lAS[nb-1]["matrix"][router1][i] != [] :
            if lAS[nb-1]["matrix"][router1][i][0] == if1:
                print(if1 + "is already attributed towards " + str(i))
                return 0
    for i in range (0, len(lAS[nb-1]["matrix"][router2])):
        if lAS[nb-1]["matrix"][router2][i] != [] :
            if lAS[nb-1]["matrix"][router2][i][0] == if2:
                print(if2 + "is already attributed towards " + str(i))
                return 0
    lAS[nb-1]["matrix"][router1][router2]=[if1,weight]
    lAS[nb-1]["matrix"][router2][router1]=[if2,weight]    


if __name__ == '__main__':
    listAS = [] #mother list that will contain the router list, config list and matrix of each AS
    with open('network.json', 'r') as openfile:
        net = json.load(openfile)

    #generate an array to store the new information about border router (ip, subnet, etc)
    borderMat = net['adjAS']
    updatedBorder = copy.deepcopy(borderMat)
    for u in range (0, len(updatedBorder)):
        for v in range (0, len(updatedBorder)):
            if updatedBorder[u][v] != 0 :
                updatedBorder[u][v] = [] #every list in the array is replaced by an empty one (we'll need them after)
    
    window(listAS, updatedBorder)





   
