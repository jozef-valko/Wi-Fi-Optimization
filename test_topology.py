#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel
import socket
import thread
import time


def socketComunnication():
    s = socket.socket()  # Create a socket object
    host = socket.gethostname()  # Get local machine name
    port = 12345  # Reserve a port for your service.
    s.connect((host, port))
    print s.recv(1024)
    s.close  # Close the socket when done


def topology():
    net = Mininet(controller=RemoteController, link=TCLink, switch=OVSKernelSwitch)

    print "Creating nodes"

    h1 = net.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1/24')
    h2 = net.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2/24')

    sw1 = net.addSwitch('sw1')
    sw2 = net.addSwitch('sw2')
    sw3 = net.addSwitch('sw3')
    sw4 = net.addSwitch('sw4')
    sw5 = net.addSwitch('sw5')
    sw6 = net.addSwitch('sw6')

    ap1 = net.addAccessPoint('ap1', ssid='AP1', mode='g', channel='1', position='30,30,0', range='30')
    ap2 = net.addAccessPoint('ap2', ssid='AP2', mode='g', channel='2', position='80,50,0', range='30')
    ap3 = net.addAccessPoint('ap3', ssid='AP3', mode='g', channel='1', position='120,100,0', range='30')
    sta1 = net.addStation('sta1', mac='00:00:00:00:00:10', ip='10.0.0.10/24', position='80,40,0')
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    net.configureWifiNodes()

    print "Associating and creating links"
    #	net.addLink(sw1, sw2)
    #	net.addLink(sw1, sw4)
    #	net.addLink(sw1, sw5)
    #	net.addLink(sw2, sw3)
    #	net.addLink(sw2, sw6)
    #	net.addLink(sw3, sw4)
    net.addLink(sw3, sw5)
    net.addLink(sw3, ap2)
    #	net.addLink(sw4, sw6)
    net.addLink(sw5, ap1)
    #	net.addLink(sw6, ap3)
    net.addLink(ap2, sta1)
    net.addLink(sw5, h1)
    net.addLink(sw3, h2)

    print "Starting network"
    net.build()
    c0.start()
    sw1.start([c0])
    sw2.start([c0])
    sw3.start([c0])
    sw4.start([c0])
    sw5.start([c0])
    sw6.start([c0])
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])

    net.plotGraph(max_x=160, max_y=160)

    net.startMobility(startTime=5)
    net.mobility(sta1, 'start', time=5, position='80.0,40.0,0.0')
    net.mobility(sta1, 'stop', time=30, position='20.0,20.0,0.0')
    net.stopMobility(stopTime=31)

    print "Running CLI"
    CLI(net)

    print "Stopping network"
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    thread.start_new_thread(socketComunnication, ())
    topology()
