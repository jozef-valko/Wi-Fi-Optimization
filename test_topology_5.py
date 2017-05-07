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

    ap1 = net.addAccessPoint('ap1', ssid='AP1', mode='g', channel='1', position='40,120,0', range='30')
    ap2 = net.addAccessPoint('ap2', ssid='AP2', mode='g', channel='6', position='80,120,0', range='30')
    ap3 = net.addAccessPoint('ap3', ssid='AP3', mode='g', channel='11', position='120,120,0', range='30')
    ap4 = net.addAccessPoint('ap4', ssid='AP4', mode='g', channel='1', position='160,120,0', range='30')
    ap5 = net.addAccessPoint('ap5', ssid='AP5', mode='g', channel='6', position='60,80,0', range='30')
    ap6 = net.addAccessPoint('ap6', ssid='AP6', mode='g', channel='11', position='100,80,0', range='30')
    ap7 = net.addAccessPoint('ap7', ssid='AP7', mode='g', channel='1', position='140,80,0', range='30')
    ap8 = net.addAccessPoint('ap8', ssid='AP8', mode='g', channel='6', position='180,80,0', range='30')
    ap9 = net.addAccessPoint('ap9', ssid='AP9', mode='g', channel='11', position='40,40,0', range='30')
    ap10 = net.addAccessPoint('ap10', ssid='AP10', mode='g', channel='1', position='80,40,0', range='30')
    ap11 = net.addAccessPoint('ap11', ssid='AP11', mode='g', channel='6', position='120,40,0', range='30')
    ap12 = net.addAccessPoint('ap12', ssid='AP12', mode='g', channel='11', position='160,40,0', range='30')

    sta1 = net.addStation('sta1', mac='00:00:00:00:00:10', ip='10.0.0.10/24')
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    net.configureWifiNodes()

    print "Associating and creating links"
    net.addLink(sw10, sw20)
    net.addLink(sw20, sw30)
    net.addLink(sw30, sw40)
    net.addLink(sw10, h1)
    net.addLink(sw20, h2)
    net.addLink(sw10, ap1)
    net.addLink(sw10, ap2)
    net.addLink(sw10, ap6)
    net.addLink(sw20, ap3)
    net.addLink(sw20, ap4)
    net.addLink(sw20, ap8)
    net.addLink(sw30, ap5)
    net.addLink(sw30, ap9)
    net.addLink(sw30, ap10)
    net.addLink(sw40, ap7)
    net.addLink(sw40, ap11)
    net.addLink(sw40, ap12)

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
    ap5.start([c0])
    ap6.start([c0])
    ap7.start([c0])
    ap8.start([c0])
    ap9.start([c0])
    ap10.start([c0])
    ap11.start([c0])
    ap12.start([c0])

    net.plotGraph(max_x=200, max_y=200)

    net.associationControl('ssf')
    net.seed(1)

    start = 2
    net.startMobility(startTime=0, model='RandomDirection', max_x=200, max_y=150, min_v=3.0, max_v=5.0)
    # net.mobility(sta2, 'start', time=start, position='0.0,0.0,0.0')
    # net.mobility(sta2, 'stop', time=start+10, position='20.0,20.0,0.0')
    # net.stopMobility(stopTime=start+11)

    thread.start_new_thread(MySocket().start, (net, ))

    print "Running CLI"
    CLI(net)

    print "Stopping network"
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()
