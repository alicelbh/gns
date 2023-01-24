import telnetlib
import json

# Opening JSON file
with open('network.json', 'r') as openfile:
 
    # Reading from json file
    net = json.load(openfile)
    
for i in range(len(net.keys()) - 1):
    nbRouters = len(net["AS" + str(i)]['inMatrix'])
    for j in range(nbRouters): 
        #we connect to the router
        host = net["AS" + str(i)]["listPorts"][j]
        print(host)
        tn = telnetlib.Telnet(host)

        file = open("as" + str(i+1) + "_routeur" + str(j) +".txt", 'r')
        read_lines = file.readlines()

        for line in read_lines:
            #we write each line in the router's console
           tn.write(line.encode('utf_8') + b"\r\n")
        file.close()
