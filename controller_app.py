import struct
import pickle
from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.ofproto import ofproto_v1_0
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
import socket
import thread
import time

apOverlap = {}
channels = [1,6,11,3,8,4,9,2,7,5,10]

def insertIntoDict(ap,apTemp,aDict):
    if not ap in aDict:
        aDict[ap] = [apTemp]
    else:
        if apTemp not in aDict[ap]:
            aDict[ap].append(apTemp)

def getStations(accessPoints):
    stations = []
    for ap in accessPoints:
        if 'stations' in accessPoints[ap]:
            for sta in range(0, len(accessPoints[ap]['stations'])):
                if accessPoints[ap]['stations'][sta] not in stations:
                    stations.append(accessPoints[ap]['stations'][sta])
    return stations

def updateApOverlap(stations, accessPoints):
    for sta in stations:
        for ap in accessPoints:
            for apTemp in accessPoints:
                if ap is not apTemp:
                    if 'stations' in accessPoints[ap] and 'stations' in accessPoints[apTemp]:
                        if sta in accessPoints[ap]['stations'] and sta in accessPoints[apTemp]['stations']:
                            insertIntoDict(ap, apTemp, apOverlap)

def changeChannel(accessPoints, apToChange):
    for ch in channels:
        if ch is not accessPoints[apToChange]['channel'][0]:
            tmp = 0
            for ap in range(0, len(apOverlap[apToChange])):
                tmp = ap
                if ch is accessPoints[apOverlap[apToChange][ap]]['channel'][0]:
                    break
            if tmp is len(apOverlap[apToChange])-1:
                accessPoints[apToChange]['channel'][0] = ch
                break

def channelCheckAndAssignment(accessPoints):
    stations = getStations(accessPoints)
    updateApOverlap(stations, accessPoints)
    for ap in apOverlap:
        for apTemp in range(0, len(apOverlap[ap])):
            if accessPoints[ap]['channel'][0] is accessPoints[apOverlap[ap][apTemp]]['channel'][0]:
                changeChannel(accessPoints, apOverlap[ap][apTemp])
    for ap in accessPoints:
        print ap + ': ' + str(accessPoints[ap])

def recv_one_message(sock):
    lengthbuf = recvall(sock, 4)
    length, = struct.unpack('!I', lengthbuf)
    return recvall(sock, length)

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

def serverSocket():
    s = socket.socket()  # Create a socket object
    host = socket.gethostname()  # Get local machine name
    port = 12345  # Reserve a port for your service.
    s.bind((host, port))  # Bind to the port

    while True:
        s.listen(5)  # Now wait for client connection.
        #try:
        while True:
            c, addr = s.accept()  # Establish connection with client.
            print 'Got connection from', addr
            while c:
                data = recv_one_message(c)
                accessPoints = pickle.loads(data)
                channelCheckAndAssignment(accessPoints)
            c.close()  # Close the connection
        #except:
            #print 'Client disconnected'

thread.start_new_thread(serverSocket, ())

class MyController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MyController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.ip_mac = {}
        self.dp_lsit = []

    def add_flow(self, datapath, in_port, dst, actions):
        ofproto = datapath.ofproto

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port, dl_dst=haddr_to_bin(dst))

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
        datapath.send_msg(mod)

    def del_flow(self, datapath, match):
        ofproto = datapath.ofproto

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_DELETE, idle_timeout=0, hard_timeout=0,
            priority=30000)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        #self.logger.info("---------------------------------------------------------")
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        if datapath not in self.dp_lsit:
            self.dp_lsit.append(datapath)

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        if pkt.get_protocol(ipv4.ipv4):
            v4 = pkt.get_protocol(ipv4.ipv4)
            l3dst = v4.dst
            l3src = v4.src
            self.ip_mac[l3src] = src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, msg.in_port)

        if self.mac_to_port[dpid].has_key(src):
            #self.logger.info("There is a port already: %s", self.mac_to_port[dpid][src])
            if self.mac_to_port[dpid][src] != msg.in_port:
                match = datapath.ofproto_parser.OFPMatch(dl_dst=haddr_to_bin(src))
                self.del_flow(datapath, match)
                #self.logger.info("flow deleted: %s %s", datapath.id, src)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = msg.in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            self.add_flow(datapath, msg.in_port, dst, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no

        ofproto = msg.datapath.ofproto
        if reason == ofproto.OFPPR_ADD:
            self.logger.info("port added %s", port_no)
        elif reason == ofproto.OFPPR_DELETE:
            self.logger.info("port deleted %s", port_no)
        elif reason == ofproto.OFPPR_MODIFY:
            self.logger.info("port modified %s", port_no)
        else:
            self.logger.info("Illeagal port state %s %s", port_no, reason)
