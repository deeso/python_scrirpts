import string, cgi, time
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


class FakeWaladecHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.print_client_info()
	def do_POST(self):
		self.print_client_info()
		captured_str = "BwAAAEWBCgGnQIlPRm3IIOcYl1ue74e_UezN8NscPi39YIIM4nhJfJR_ARRzhIjAI8TIAkkyflgdvfbkb3er453PGjFuIY-Nr-W81KlJvcSKGsuYYg"
		self.send_response(200)
		self.send_header('Server','nginx/0.6.33')
		self.send_header('Date','Sat, 28 Feb 2009 14:10:45 GMT')
		self.send_header('Transfer-Encoding','chunked')
		self.send_header('Connection','keep-alive')
		self.send_header('X-Powered-By','PHP/5.2.8')
		self.end_headers()
		
		self.wfile.write("72\r\n")
		self.wfile.write(captured_str+"\r\n")
		self.wfile.write("0\r\n")
	def print_client_info(self):
		print "Recieved request with the following stuffz"
		print "Client Address %s"%str(self.client_address)
		print "Command: %s"%str(self.command)
		print "Path: %s"%str(self.path)
		print "Headers: %s"%str(self.headers )

def main():
	try:
		server = HTTPServer(('',8080), FakeWaladecHandler)
		print 'started fake Waladec Serve....'
		server.serve_forever()
	except KeyboardInterrupt:
		print "^C recieved"
		server.socket.close()

if __name__== '__main__':
	main()
