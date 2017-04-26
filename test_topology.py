#!/usr/bin/python
import struct

import pickle

import subprocess
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch, OVSKernelAP
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info, output
import socket
import thread
import time

def insertIntoDict(ap,station,aDict):
    if not ap in aDict:
        aDict[ap] = [station]
    else:
        aDict[ap].append(station)

def getStationsInRange(net):
    stationsInRange = {}
    for ap in net.accessPoints:
        for sta in ap.params['stationsInRange']:
            insertIntoDict(ap.name, sta.name, stationsInRange)
    return stationsInRange

def send_one_message(sock, data):
    length = len(data)
    sock.send(struct.pack('!I', length))
    sock.send(data)

def socketComunnication(net):
    s = socket.socket()  # Create a socket object
    host = socket.gethostname()  # Get local machine name
    port = 12345  # Reserve a port for your service.
    try:
        s.connect((host, port))
        print 'Connected to algorithm application'
        while 1:
            stationsInRange = getStationsInRange(net)
            data = pickle.dumps(stationsInRange)
            send_one_message(s,data)
            time.sleep(1)
        #print s.recv(1024)
        #s.close  # Close the socket when done
    except:
        print 'Can\'t connect to algorithm application'

def execute(cmd):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (result, error) = process.communicate()

    rc = process.wait()

    if rc != 0:
        print "Error: failed to execute command:", cmd
        print error
    return result

def channelChange(channel):
    time.sleep(10)
    fileToChange = execute("ps -aux | grep ap1-wlan1.apconf | cut -d ':' -f3 | cut -d ' ' -f4 | head -n1")
    execute("sudo sed -i 's/channel=.*/channel=" + str(channel) + "/' " + fileToChange)
    execute("sudo kill `ps -aux | grep ap1-wlan1.apconf | tr -s ' ' | cut -d ' ' -f2 | head -n1`")
    execute("sudo hostapd -B " + fileToChange)
    #print "Channel changed"

def topology():
    net = Mininet(controller=RemoteController, link=TCLink, accessPoint=OVSKernelAP, switch=OVSKernelSwitch, useWmediumd=True)
    #net = Mininet(controller=RemoteController, link=TCLink, accessPoint=OVSKernelAP, switch=OVSKernelSwitch)

    print "Creating nodes"

    h1 = net.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1/24')
    h2 = net.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2/24')

    sw10 = net.addSwitch('sw10')
    sw20 = net.addSwitch('sw20')
    sw30 = net.addSwitch('sw30')
    sw40 = net.addSwitch('sw40')

    ap1 = net.addAccessPoint('ap1', ssid='AP1', mode='g', channel='1', position='40,60,0', range='30')
    ap2 = net.addAccessPoint('ap2', ssid='AP2', mode='g', channel='6', position='60,60,0', range='30')
    ap3 = net.addAccessPoint('ap3', ssid='AP3', mode='g', channel='11', position='40,40,0', range='30')
    ap4 = net.addAccessPoint('ap4', ssid='AP4', mode='g', channel='1', position='60,40,0', range='30')
    #ap5 = net.addAccessPoint('ap5', ssid='AP5', mode='g', channel='6', position='30,30,0', range='30')


    sta1 = net.addStation('sta1', mac='00:00:00:00:00:10', ip='10.0.0.10/24', position='50,50,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:20', ip='10.0.0.20/24', position='20,20,0')
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    net.configureWifiNodes()

    print "Associating and creating links"
    net.addLink(sw10, sw20)
    net.addLink(sw20, sw30)
    net.addLink(sw30, sw40)
    net.addLink(sw10, h1)
    net.addLink(sw20, h2)
    net.addLink(sw10, ap1)
    net.addLink(sw20, ap2)
    net.addLink(sw30, ap3)
    net.addLink(sw40, ap4)
    #net.addLink(sw3, ap5)
    net.addLink(ap1, sta1)

    print "Starting network"
    net.build()
    c0.start()
    sw10.start([c0])
    sw20.start([c0])
    sw30.start([c0])
    sw40.start([c0])
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])
    ap4.start([c0])
    #ap5.start([c0])

    net.plotGraph(max_x=100, max_y=100)

    # start = 2
    # net.startMobility(startTime=start)
    # net.mobility(sta2, 'start', time=start, position='0.0,0.0,0.0')
    # net.mobility(sta2, 'stop', time=start+10, position='20.0,20.0,0.0')
    # net.stopMobility(stopTime=start+11)

    thread.start_new_thread(socketComunnication, (net, ))

    print "Running CLI"
    CLI(net)

    print "Stopping network"
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    #thread.start_new_thread(channelChange, (6,))
    topology()
