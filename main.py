import sys
import json
import copy
import time
import telnetlib
import io

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot


def configureInsideProtocols(asName):
    listR = [] #list of routers in the AS
    listC = [] #list of the commands for each router in the AS

    asMask = "/" +net[asName]['mask']
    asMat = net[asName]['inMatrix']
    asNb = str(net[asName]['asNumber']) 
    asProt = net[asName]['protocol']
    asPrefix = str(net[asName]['prefix'])
    matLen = len(net[asName]['inMatrix'])
    linkNumber = 0

    for i in range (0, matLen):
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

        #configure the interfaces of the border routers 
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
                        updatedBorder[int(asNb)-1][b].append(borderAsDic)
                        textBorder += "interface " + borderAsDic["interface"] + "\nipv6 enable" + "\nipv6 address " + borderAsDic["@ip"] + asMask + "\nno shutdown\nexit\n"    

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

    listAS.append(asSpecifications)

def configureBorderProtocol():
    adjAS = net['adjAS']
    for n in range(0, len(listAS)):
        mask = "/" + str(net['AS' + str((n+1))]['mask'])
        ####### configure iBGP
        for i in range(0, len(listAS[n]["routers"])):
            listAS[n]["config"][i] += "router bgp " + str(n+1) +"\nno bgp default ipv4-unicast\nbgp router-id " + listAS[n]["routers"][i]["routerID"] + "\n"
            for j in range(0, len(listAS[n]["routers"])):
                if i != j:
                    listAS[n]["config"][i] += "neighbor " + listAS[n]["routers"][j]["loopBackAddress"] +" remote-as " +str(n+1)+"\nneighbor " + listAS[n]["routers"][j]["loopBackAddress"] +" update-source Loopback0\n"
            listAS[n]["config"][i] += "address-family ipv6 unicast\n"
            for j in range(0, len(listAS[n]["routers"])):
                if i!=j:
                    listAS[n]["config"][i] += "neighbor " + listAS[n]["routers"][j]["loopBackAddress"] +" activate\n"
            for j in range(0, len(listAS[n]["matrix"][i])):
                if listAS[n]["matrix"][i][j] != 0:
                    listAS[n]["config"][i] += "network " + listAS[n]["matrix"][i][j]["@subnet"] + mask +"\n"
            listAS[n]["config"][i] += "exit\n"
        ####### configure eBGP
        for i in range(0, len(adjAS[n])):
            if (adjAS[n][i]) != 0:
                for y in range(0, len(updatedBorder[n][i])):
                    router = updatedBorder[i][n][y]['router']
                    address =  updatedBorder[i][n][y]['@ip']

                    listAS[n]["config"][router] += "neighbor " + address + " remote-as " + str(i+1) + "\naddress-family ipv6 unicast\nneighbor " + address + " activate\nnetwork " + updatedBorder[n][i][y]['@subnet'] + "\nexit\n"




def window():
    app = QApplication(sys.argv)
    widget = QWidget()

    button1 = QPushButton(widget)
    button1.setText("Generate files")
    button1.move(64,32)
    button1.clicked.connect(button1_clicked)

    # button2 = QPushButton(widget)
    # button2.setText("Send config")
    # button2.move(64,64)
    # button2.clicked.connect(button2_clicked)

    widget.setGeometry(50,50,320,200)
    widget.setWindowTitle("Dudu")
    widget.show()
    sys.exit(app.exec_())


def button1_clicked():
    print("Button 1 clicked")
   #implement the inside protocols for each AS
    for key in net: #for each 
        if (key!="adjAS"):
            configureInsideProtocols(key)

    configureBorderProtocol()

    #generate the text files
    for i in range (0, len(listAS)):
        for r in range (0, len(listAS[i]['config'])):
            f = open("configs/as"+ str(i+1) + "_router" + str(r+1) +".txt", "w")
            f.write(listAS[i]['config'][r])
    
    #telnet
    for i in range(len(net.keys()) - 1):

        nbRouters = len(net["AS" + str(i+1)]['inMatrix'])
        for j in range(nbRouters): 
            time.sleep(0.1)
            #we connect to the router
            
            port = net["AS" + str(i+1)]["listPorts"][j]
            print(port)
            tn = telnetlib.Telnet("localhost", port)
            buf = io.StringIO(listAS[i]["config"][j])
            read_lines = buf.readlines()

            for line in read_lines:
                print(line)
                #we write each line in the router's console
                tn.write(b"\r\n")
                tn.write(line.encode('utf_8') + b"\r\n")
                time.sleep(0.1)
            #file.close()
   
if __name__ == '__main__':
    listAS = [] #list that will contain the router list, config list and matrix of each AS
    with open('network.json', 'r') as openfile:
        net = json.load(openfile)

    #generate an array to store the new information about border router (ip, subnet, etc)
    borderMat = net['adjAS']
    updatedBorder = copy.deepcopy(borderMat)
    for u in range (0, len(updatedBorder)):
        for v in range (0, len(updatedBorder)):
            if updatedBorder[u][v] != 0 :
                updatedBorder[u][v] = []
    window()
