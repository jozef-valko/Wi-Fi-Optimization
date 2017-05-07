#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch, OVSKernelAP
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel
import thread
from my_socket_with_channel_change import MySocket

def topology():
    net = Mininet(controller=RemoteController, link=TCLink, accessPoint=OVSKernelAP, switch=OVSKernelSwitch, useWmediumd=True)

    print "Creating nodes"

    h1 = net.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1/24')
    h2 = net.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2/24')

    sw10 = net.addSwitch('sw10')
    sw20 = net.addSwitch('sw20')
    sw30 = net.addSwitch('sw30')
    sw40 = net.addSwitch('sw40')

    ap1 = net.addAccessPoint('ap1', ssid='AP1', mode='g', channel='1', position='40,60,0', range='30')
    ap2 = net.addAccessPoint('ap2', ssid='AP2', mode='g', channel='1', position='60,60,0', range='30')

    sta1 = net.addStation('sta1', mac='00:00:00:00:00:10', ip='10.0.0.10/24', position='50,70,0')
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    net.configureWifiNodes()

    print "Associating and creating links"
    net.addLink(sw10, sw20)
    net.addLink(sw20, sw30)
    net.addLink(sw10, sw40)
    net.addLink(sw10, h1)
    net.addLink(sw20, h2)
    net.addLink(sw10, ap1)
    net.addLink(sw20, ap2)

    print "Starting network"
    net.build()
    c0.start()
    sw10.start([c0])
    sw20.start([c0])
    sw30.start([c0])
    sw40.start([c0])
    ap1.start([c0])
    ap2.start([c0])

    net.plotGraph(max_x=100, max_y=100)

    # start = 2
    # net.startMobility(startTime=start)
    # net.mobility(sta1, 'start', time=start, position='0.0,0.0,0.0')
    # net.mobility(sta1, 'stop', time=start+10, position='20.0,20.0,0.0')
    # net.stopMobility(stopTime=start+11)

    thread.start_new_thread(MySocket().start, (net, ))

    print "Running CLI"
    CLI(net)

    print "Stopping network"
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()
