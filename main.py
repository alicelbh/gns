import json
import copy
 
# Opening JSON file
with open('network.json', 'r') as openfile:
 
    # Reading from json file
    net = json.load(openfile)

listAS = []

borderMat = net['adjAS']
updatedBorder = copy.deepcopy(borderMat)

for u in range (0, len(updatedBorder)):
    for v in range (0, len(updatedBorder)):
        if updatedBorder[u][v] != 0 :
            updatedBorder[u][v] = []

def createRouters(asName):
    listR = [] #list of routers in the AS
    listC = [] #list of the commands for each router in the AS
    asMat = net[asName]['inMatrix']
    asNb = str(net[asName]['asNumber']) 
    asProt = net[asName]['protocol']
    asPrefix = str(net[asName]['prefix'])
    matLen = len(net[asName]['inMatrix'])
    linkNumber = 0

    for i in range (0, matLen):
        routerName = asNb + str(i)
        routerNb = asNb + '.0.0.' + str(i)
        loopBackAddress = asNb + "::" + str(i)
        listR.append([routerNb, routerName, loopBackAddress]) #add router number, name and loopback address to the list of routers

        borderAsDic = {}
        textBorder = ""

         #### check if it's a border router
        for b in range (0, len(borderMat)):
            if borderMat[int(asNb)-1][b] != 0: #check if there exist a connection betwteen our AS and another one
                l = []
                for z in range (0,len(borderMat[int(asNb)-1][b]), 3): #if there exists one, check if the number of the router i is in the border matrix
                    if borderMat[int(asNb)-1][b][z] == i: 
                        borderAsDic = {
                            "router" : i,
                            "interface" : borderMat[int(asNb)-1][b][z+1],
                            "@ip" : str(borderMat[int(asNb)-1][b][z+2])  + ":" + asNb + "/64",
                            "@subnet" :  borderMat[int(asNb)-1][b][z+2] + ":" +"/64"
                        }
                        updatedBorder[int(asNb)-1][b].append(borderAsDic)
                        textBorder += "interface " + borderAsDic["interface"] + "\nipv6 enable" + "\nipv6 address " + borderAsDic["@ip"] + "\nno shutdown\nexit\n"    

        ######## declare each interfaces, create each IP
        for j in range(i, matLen):
            if asMat[i][j] != 0:
                subNetAddress = asPrefix +  asNb + ":" + str(linkNumber) + "::/64" 
                inAddress = asPrefix +  asNb + ":" + str(linkNumber) + "::" + "1/64"
                inAddressNeighbor = asPrefix +  asNb + ":" + str(linkNumber) + "::" + "2/64"
                
                if asProt == 'RIP' :
                    asMatDic = {
                        "interface" : asMat[i][j][0],
                        "@ip" : inAddress,
                        "@subnet" :  subNetAddress
                    }
                    asMatDicNeighbor = {
                        "interface" : asMat[j][i][0],
                        "@ip" : inAddressNeighbor,
                        "@subnet": subNetAddress
                    }
                elif asProt == "OSPF":
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
              

                asMat[i][j] = asMatDic
                asMat[j][i] = asMatDicNeighbor
                linkNumber += 1


        ######## add command to list of texts
        text = "enable\nconfigure terminal\nipv6 unicast-routing\n"
        if(asProt == 'RIP'):
            text += 'ipv6 router rip ' + routerName + "\nexit\n"
            for a in range (0, matLen): #configure all of the physical interfaces
                if asMat[i][a] !=0:
                    text += "interface " + asMat[i][a]["interface"] + "\nipv6 enable" + "\nipv6 address " + asMat[i][a]["@ip"] + "\nno shutdown\nipv6 rip " + routerName + " enable \nexit\n"
            text+= "interface loopback 0\nipv6 enable\nipv6 address " + loopBackAddress + "/128" + "\nno shutdown\nipv6 rip " + routerName + " enable \nexit\n"
            text+= textBorder
            if borderAsDic != {}:
                text+= ""

        elif(asProt == 'OSPF'):
            text += 'ipv6 router ospf 1\nrouter-id ' + routerNb + "\nexit\n"
            for a in range (0, matLen): #configure all of the physical interfaces
                if asMat[i][a] !=0:
                    text+= "interface " + asMat[i][a]["interface"] + "\nipv6 enable" + "\nipv6 address " + asMat[i][a]["@ip"] + "\nno shutdown\nipv6 ospf 1 area 0\nexit\n"
            text+= "interface loopback 0\nipv6 enable\nipv6 address " + loopBackAddress + "/128" + "\nno shutdown\nipv6 ospf 1 area 0 \nexit\n"
            text+= textBorder
        #print(text)
        listC.append(text) #add command to list

    asSpecifications = {
        "routers" : listR,
        "config" : listC,
        "matrix" : asMat
    }
    listAS.append(asSpecifications)


for key in net: #for each 
    if (key!="adjAS"):
        createRouters(key)


#où s'arrête un préfix ipv6 ? pour les routeurs de bordure
# # faire la liste des routeurs de bordure

def configureBorderProtocol():
    adjAS = net['adjAS']
    networkPrefix = "toto" #sous réseaux locaux dans l'AS auquel il est connecté 
    gatewayAddress = "tata" #adresse du mec en face réseau entre as
    gatewayPrefix = "tutu" #préfix réseau entre les 2 as
    for n in range(0, len(listAS)):
        ####### configure iBGP
        for i in range(0, len(listAS[n]["routers"])):
            listAS[n]["config"][i] += "configure terminal\nrouter bgp " + str(n+1) +"\nno bgp default ipv4-unicast\nbgp router-id " + listAS[n]["routers"][i][0] + "\n"
            for j in range(0, len(listAS[n]["routers"])):
                if i != j:
                    print(listAS[n]["routers"][2])
                    listAS[n]["config"][i] += "neighbor " + listAS[n]["routers"][j][2] +" remote-as " +str(n+1)+"\nneighbor " + listAS[n]["routers"][j][2] +" update-source Loopback0\n"
            listAS[n]["config"][i] += "address-family ipv6 unicast\n"
            for j in range(0, len(listAS[n]["routers"])):
                if i!=j:
                    listAS[n]["config"][i] += "neighbor " + listAS[n]["routers"][j][2] +" activate\n"
            for j in range(0, len(listAS[n]["matrix"][i])):
                if listAS[n]["matrix"][i][j] != 0:
                    listAS[n]["config"][i] += "network " + listAS[n]["matrix"][i][j]["@subnet"] +"\n"
            listAS[n]["config"][i] += "exit\n"
        ####### configure eBGP
        for i in range(0, len(adjAS[n])):
            if (adjAS[n][i]) != 0:
                for y in range(0, len(updatedBorder[n][i])):
                    router = updatedBorder[i][n][y]['router']
                    address =  updatedBorder[i][n][y]['@ip']

                    listAS[n]["config"][router] += "neighbor " + address + " remote-as " + str(i+1) + "\naddress-family ipv6 unicast\nneighbor " + address + " activate\nnetwork " + updatedBorder[n][i][y]['@subnet'] + "\nexit\n"


print(updatedBorder)

# for key in net: #for each 
#     if (key!="adjAS"):
#         createRouters(key)

configureBorderProtocol()

for i in range (0, len(listAS)):
    for r in range (0, len(listAS[i]['config'])):
        f = open("configs/as"+ str(i+1) + "_routeur" + str(r) +".txt", "w")
        f.write(listAS[i]['config'][r])
