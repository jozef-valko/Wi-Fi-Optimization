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
                print 'changeChannel:'
                print 'AP to change: ' + apToChange + ': ' + str(ch)
                print apOverlap
                break

def lastChance(accessPoints, list, neighborsList):
    channel = accessPoints[list[0]]['channel'][0]
    for ap in neighborsList:
        tmp = 0
        for apTemp in range(0, len(apOverlap[ap])):
            tmp = apTemp
            if list[0] is not apOverlap[ap][apTemp]:
                if list[1] is not apOverlap[ap][apTemp]:
                    if channel is accessPoints[apOverlap[ap][apTemp]]['channel'][0]:
                        break
        if tmp is len(apOverlap[ap]) - 1:
            if list[0] not in apOverlap[ap] or list[1] not in apOverlap[ap]:
                tmpChannel = accessPoints[ap]['channel'][0]
                accessPoints[ap]['channel'][0] = channel
                result = False
                for apInList in list:
                    for ch in range(0, 3):
                        if channels[ch] is not accessPoints[apInList]['channel'][0]:
                            tmp = 0
                            for apTempInList in range(0, len(apOverlap[apInList])):
                                tmp = apTempInList
                                if channels[ch] is accessPoints[apOverlap[apInList][apTempInList]]['channel'][0]:
                                    break
                            if tmp is len(apOverlap[apInList]) - 1:
                                accessPoints[apInList]['channel'][0] = channels[ch]
                                print 'lastChance'
                                print 'AP to change: ' + ap + ': ' + str(channel)
                                print 'tryBest in lastChance:'
                                print 'AP to change: ' + apInList + ': ' + str(channels[ch])
                                result = True
                if result is True:
                    return True
                accessPoints[ap]['channel'][0] = tmpChannel
    return False

def tryBest(accessPoints, list):
    for ap in list:
        for ch in range(0, 3):
            if channels[ch] is not accessPoints[ap]['channel'][0]:
                tmp = 0
                for apTemp in range(0, len(apOverlap[ap])):
                    tmp = apTemp
                    if channels[ch] is accessPoints[apOverlap[ap][apTemp]]['channel'][0]:
                        break
                if tmp is len(apOverlap[ap])-1:
                    accessPoints[ap]['channel'][0] = channels[ch]
                    print 'tryBest:'
                    print 'AP to change: ' + ap + ': ' + str(channels[ch])
                    return True
    neighborsList = []
    for ap in list:
        for apTemp in range(0, len(apOverlap[ap])):
            neighborsList.append(apOverlap[ap][apTemp])
    if lastChance(accessPoints, list, neighborsList) is False:
        return False
    return True

def channelOptimization(accessPoints):
    stations = getStations(accessPoints)
    updateApOverlap(stations, accessPoints)
    for ap in apOverlap:
        for apTemp in range(0, len(apOverlap[ap])):
            if accessPoints[ap]['channel'][0] is accessPoints[apOverlap[ap][apTemp]]['channel'][0]:
                collideList = [ap]
                collideList.append(apOverlap[ap][apTemp])
                if tryBest(accessPoints, collideList) is False:
                    changeChannel(accessPoints, apOverlap[ap][apTemp])
                print'-------------------------------------------------------------'


def send_one_message(sock, data):
    length = len(data)
    sock.send(struct.pack('!I', length))
    sock.send(data)

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
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Vytvorenie soketu
    host = socket.gethostname()  # Nazov lokalneho stroja
    port = 10000  # Rezervovanie portu pre komunikaciu
    s.bind((host, port))  # Priradenie hosta na port

    while True:
        s.listen(5)  # Cakanie na pripojenie klienta
        print 'Waiting for connection...'
        c, addr = s.accept()  # Vytvorenie spojenia s klientom
        try:
            print 'Got connection from', addr
            while True:
                data = recv_one_message(c)
                accessPoints = pickle.loads(data)

                channelOptimization(accessPoints)

                data = pickle.dumps(accessPoints)
                send_one_message(c,data)
        finally:
            c.close()
            print 'Client disconnected'

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
