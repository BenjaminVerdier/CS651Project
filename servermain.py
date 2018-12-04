from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import pickle
import sys
sys.path.append('python-chord')
import local_reddit

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
	if (len(sys.argv) > 2):
		__chord_host = ("127.0.0.1", int(sys.argv[2]))

	def __parse_request(self):
		"""Builds a command for the chord ring from the http request we receive
		Args:
			N/A
		Returns:
			A string to be sent to the chord ring
		"""
		if self.path == '/':
			#landing page
			return "get_posts_from all 10 hot"

		#self.path should follow the form:
		#posts/subreddit/number_of_posts/ordering
		#or:
		#comments/post/number_of_comments/ordering
		#If no ordering, we default to top, if no number of posts, we default to 10
		splitRequest = self.path[1:].split('/')
		print(self.path)
		command = ""

		if splitRequest[0] == "posts":
			command = "get_posts_from "
		else:
			command = "" #change this to the right command

		command = command + splitRequest[1] + " "
		if len(splitRequest) > 2:
			command = command + splitRequest[2] + " "
		else:
			command = command + "10 "

		if len(splitRequest) > 3:
			command = command + splitRequest[3] + " "
		else:
			command = command + "top "
		return command


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
		for submission in result:
			self.wfile.write(bytes("<p><a href=\"" + str(submission.url) + "\">" + str(submission.title) + "</a> ("+ "<a href=\"https://www.reddit.com/r/" + str(submission.parent) + "\">r/" + str(submission.upperLevelId) + "</a>" + ")</p>", "utf-8"))
		#self.wfile.write(bytes("<p>%s</p>" % result, "utf-8"))
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
		command = self.__parse_request()
		s.sendall((command + "\r\n").encode()) # Not the right value
		result = pickle.loads(s.recv(10000))
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
			self.__respond_failure
		else:
			if '/favicon.ico' in self.path:
				self.send_response(200)
				self.send_header("Content-type", "text/html")
				self.end_headers()
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
