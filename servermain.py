from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import sys

# We are local only for the moment
hostName = "localhost"

# Default to standard HTTP port
if (len(sys.argv) > 1):
	serverPort = int(sys.argv[1])
else:
	serverPort = 80

class ChordRingAwareHTTPRequestHandler(BaseHTTPRequestHandler):
	"""An HTTP Request Handler that forwards requests to a chord ring
	Will return a 503 error unless it is able to contact the chord ring
	
	To use:
	>>> webServer = HTTPServer((hostName, serverPort), ChordRingAwareHTTPRequestHandler)
	"""
	
	__chord_host = None
	
	def init_chord(self, destination):
		"""
		Args:
			destination (2-tuple (host, port)): the location of a node in the Chord ring
		Returns:
			N/A
		"""
		self.__chord_host = destination
	
	def __respond_failure(self):
		"""Write a 503 response
		Args:
			N/A
		Returns:
			N/A
		"""
		self.send_response(503)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(bytes("<html><head><title>Local Reddit</title></head><body>", "utf-8"))
		self.wfile.write(bytes("<h1>503: Chord ring not available; try again later</h1>", "utf-8"))
		self.wfile.write(bytes("</body></html>", "utf-8"))
	
	def __respond_get_from_chord(self):
		"""Write a 200 response with the body of the query result
		Args:
			N/A
		Returns:
			N/A
		"""
		result = self.__query_chord()
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(bytes("<html><head><title>Local Reddit</title></head><body>", "utf-8"))
		self.wfile.write(bytes("<p>%s</p>" % result, "utf-8"))
		self.wfile.write(bytes("</body></html>", "utf-8"))
	
	def __query_chord(self):
		"""Query the chord ring and return the response
		Args:
			N/A
		Returns:
			(string) The response from the chord ring
		"""
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(self.__chord_host)
		s.sendall(("command" + "\r\n").encode()) # Not the right value
		result = s.recv(10000).decode()
		s.close()
		return result
	
	def do_GET(self):
		"""Serve the GET from the Chord ring (if alive)
		Args:
			N/A
		Returns:
			N/A
		"""
		if not self.__chord_host:
			self.__respond_failure()
		else:
			self.__respond_get_from_chord()

if __name__ == "__main__":
	webServer = HTTPServer((hostName, serverPort), ChordRingAwareHTTPRequestHandler)
	print("Server started http://%s:%s" % (hostName, serverPort))
	try:
		webServer.serve_forever()
	except KeyboardInterrupt:
		pass

	webServer.server_close()
	print("Server stopped.")