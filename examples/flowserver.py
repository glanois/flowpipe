import sys
import inspect
import logging
import socket
import string

import flowpipe


class Application(flowpipe.INode):
    def __init__(self, **kwargs):
        super(Application, self).__init__(**kwargs)
        flowpipe.InputPlug('input', self)
        flowpipe.OutputPlug('output', self)

    def compute(self, **args):
        # Echo the input back as the output.
        return { 'output' : args['input'] }


class TcpServer:
    """ TCP/IP server.
        Example usage:

        t = TcpServer()
        t.bind('localhost', 51001)
        while True:
            t.accept()
            while True:
                data = t.recv()
                if data:
                    # Do something with the data.

                    # Send something back
                    t.sendall('blah blah blah')
                else:
                    # No data received.
                    break
        t.close()
    """
    def __init__(self):
        self._input = None
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Avoid "OSError: [Errno 98] Address already in use" when restarting.
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._connection = None

    def bind(self, address, port):
        self._sock.bind( (address, port) )
        logging.info('TcpServer::__init__() - bound to %s:%d' % (address, port))
        self._sock.listen(1)
        logging.info('TcpServer::__init__() - called socket.listen(1)')
        
    def accept(self):
        logging.info('TcpServer::accept() - calling socket.accept()')
        self._connection, client_address = self._sock.accept()
        logging.info('TcpServer::accept() - accepted connection from %s' % str(client_address))

    def recv(self):
        data = self._connection.recv(1024)
        if data:
            logging.info('TcpServer::recv() - socket.recv() returned %d bytes.' % len(data))
        else:
            logging.info('TcpServer::recv() - socket.recv() no data.')
        return data

    def sendall(self, data):
        self._connection.sendall(data)
        logging.info('TcpServer::sendall() - socket.sendall() sent %d bytes' % len(data))

    def close(self):
         self._connection.close()


class FlowServer(TcpServer):
    def __init__(self, address, port):
        super(TcpServer, self).__init__()
        self._address = address
        self._port = port

    def run(self):
        g = flowpipe.Graph()
        app = Application(graph=g)

        t = TcpServer()
        t.bind(self._address, self._port)

        shutdown = False
        while not shutdown:
            t.accept()
            while True:
                data = t.recv()
                if data:
                    s = data.decode('ascii').rstrip()
                    if s == 'shutdown':
                        shutdown = True
                        t.close()
                        break
                    else:
                        app.inputs['input'].value = data
                        g.evaluate()
                        t.sendall(app.outputs['output'].value)
                else:
                    # No data received.
                    break
        

def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    # TCP/IP socket server. Test with telnet.
    # telnet 127.0.0.1 51001
    f = FlowServer('localhost', 51001)
    f.run()

    return 0

if __name__ == '__main__':
    sys.exit(main())
