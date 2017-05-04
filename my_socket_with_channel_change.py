#!/usr/bin/python
import socket
import pickle
import struct
import time
import subprocess

class MySocket():

    def start(self, net):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
        host = socket.gethostname()  # Get local machine name
        port = 10000  # Reserve a port for your service.

        s.connect((host, port))
        try:
            print 'Connected to algorithm application'
            while 1:
                accessPoints = self.getAccessPoints(net)
                data = pickle.dumps(accessPoints)
                self.send_one_message(s, data)

                data = self.recv_one_message(s)
                accessPoints = pickle.loads(data)
                self.updateChanges(accessPoints, net)

                time.sleep(1)
        finally:
            s.close  # Close the socket when done
            print 'Socket closed'

    def insertIntoDict(self, ap, station, aDict):
        if not ap in aDict:
            aDict[ap] = {}
        if not 'stations' in aDict[ap]:
            aDict[ap]['stations'] = [station]
        else:
            aDict[ap]['stations'].append(station)

    def getAccessPoints(self, net):
        accessPoints = {}
        for ap in net.accessPoints:
            for sta in ap.params['stationsInRange']:
                self.insertIntoDict(ap.name, sta.name, accessPoints)
            if not ap.name in accessPoints:
                accessPoints[ap.name] = {}
            accessPoints[ap.name]['channel'] = ap.params['channel']
        return accessPoints

    def updateChanges(self, accessPoints, net):
        for ap in accessPoints:
            for apNet in net.accessPoints:
                if ap == apNet.name:
                    if accessPoints[ap]['channel'][0] is not apNet.params['channel'][0]:
                        self.changeChannel(ap, accessPoints[ap]['channel'][0])
                        apNet.params['channel'][0] = accessPoints[ap]['channel'][0]
                        apNet.params['frequency'][0] = str(
                            2.412 + (float(accessPoints[ap]['channel'][0] - 1) * 5 / 1000))

    def execute(self, cmd):
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (result, error) = process.communicate()
        rc = process.wait()
        if rc != 0:
            print "Error: failed to execute command:", cmd
            print error
        return result

    def changeChannel(self, ap, channel):
        fileToChange = self.execute("ps -aux | grep " + str(ap) + "-wlan1.apconf | grep hostapd | cut -d ':' -f3 | cut -d ' ' -f4 | head -n1")
        self.execute("sudo sed -i 's/channel=.*/channel=" + str(channel) + "/' " + fileToChange)
        self.execute("sudo kill `ps -aux | grep " + str(ap) + "-wlan1.apconf | tr -s ' ' | cut -d ' ' -f2 | head -n1`")
        self.execute("sudo hostapd -B " + fileToChange)
        #print 'channel changed on ' + str(ap) + ': ' + str(channel)

    def send_one_message(self, sock, data):
        length = len(data)
        sock.send(struct.pack('!I', length))
        sock.send(data)

    def recv_one_message(self, sock):
        lengthbuf = self.recvall(sock, 4)
        length, = struct.unpack('!I', lengthbuf)
        return self.recvall(sock, length)

    def recvall(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
        return buf