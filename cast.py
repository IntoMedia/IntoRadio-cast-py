import vlc
from http.server import BaseHTTPRequestHandler, HTTPServer
import ssl
import time
import json
import hashlib


hostName = "0.0.0.0"
serverPort = 9845

d_token = ''
d_last = 0

try:
	instance = vlc.Instance()
except NameError:
	raise Exception("ERROR: VLC is not installed")


player = instance.media_player_new()

class MyServer(BaseHTTPRequestHandler):
	def do_OPTIONS(self):
		self.send_response(200, "ok")
		self.send_header('Access-Control-Allow-Origin', '*')
		self.end_headers()
		
		
	def do_GET(self):
		global d_token
		if self.path == "/ircast/discover":
			self.send_response(200)
			self.send_header('Access-Control-Allow-Origin', '*')
			self.send_header("Content-type", "application/json")
			self.end_headers()
			paired = 'true'
			if d_token == '' :
				paired = 'false'
			
			self.wfile.write(bytes('{"name":"Raspberry Pi","type":4,"paired":'+paired+',"version":1}', "utf-8"))
			
	def do_POST(self):
		global d_token
		global d_last
		global player

		content_len = int(self.headers.get('Content-Length'))
		post_body = self.rfile.read(content_len)
		data = json.loads(post_body)
		timestamp = int(time.time())
		
		if self.path == "/ircast/pairing":
			if d_token != '' :
				if d_last < timestamp-60 : 
					d_token = ''
					
			self.send_response(200)
			self.send_header('Access-Control-Allow-Origin', '*')
			self.send_header("Content-type", "application/json")
			self.end_headers()
			
			if d_token == '' :
				d_token = data['token']
				self.wfile.write(bytes('{"success":true}', "utf-8"))
			else:
				self.wfile.write(bytes('{"success":false}', "utf-8"))
				
		else:
		
			token = str(data['time'])+''+d_token;
			
			_hash = hashlib.md5(token.encode()).hexdigest()
			
			if _hash != data['hash'] or data['time']<timestamp-30 :
				self.send_response(200)
				self.send_header('Access-Control-Allow-Origin', '*')
				self.send_header("Content-type", "application/json")
				self.end_headers()
				self.wfile.write(bytes('{"success":false}', "utf-8"))
			
			else:
				d_last = timestamp
				if self.path == "/ircast/media":
					self.send_response(200)
					self.send_header('Access-Control-Allow-Origin', '*')
					self.send_header("Content-type", "application/json")
					self.end_headers()
					
					player.set_time(0)
					media = instance.media_new(data['media'])
					player.set_media(media)
					player.play()
					
					self.wfile.write(bytes('{"success":true}', "utf-8"))
					
				elif self.path == "/ircast/status":
					self.send_response(200)
					self.send_header('Access-Control-Allow-Origin', '*')
					self.send_header("Content-type", "application/json")
					self.end_headers()
					
					playing = 'false'
					if player.is_playing() :
						playing = 'true'
			
					
					self.wfile.write(bytes('{"playing":'+playing+',"volume":'+str(player.audio_get_volume()/100)+',"duration":'+str(player.get_length()/1000)+',"position":'+str(player.get_time()/1000)+'}', "utf-8"))
					
				elif self.path == "/ircast/playorpause":
					self.send_response(200)
					self.send_header('Access-Control-Allow-Origin', '*')
					self.send_header("Content-type", "application/json")
					self.end_headers()
					
					if player.is_playing() :
						player.pause()
					else:
						player.play()
					
					self.wfile.write(bytes('{"success":true}', "utf-8"))
					
				elif self.path == "/ircast/volume":
					self.send_response(200)
					self.send_header('Access-Control-Allow-Origin', '*')
					self.send_header("Content-type", "application/json")
					self.end_headers()
					
					player.audio_set_volume(int(data['volume']*100))
					
					self.wfile.write(bytes('{"success":true}', "utf-8"))
				elif self.path == "/ircast/seek":
					self.send_response(200)
					self.send_header('Access-Control-Allow-Origin', '*')
					self.send_header("Content-type", "application/json")
					self.end_headers()
					
					player.set_time(int(data['position']*1000))
					
					self.wfile.write(bytes('{"success":true}', "utf-8"))
				elif self.path == "/ircast/disconnect":
					self.send_response(200)
					self.send_header('Access-Control-Allow-Origin', '*')
					self.send_header("Content-type", "application/json")
					self.end_headers()
					
					player.stop()
					d_token = ''
					d_last = 0
					
					self.wfile.write(bytes('{"success":true}', "utf-8"))
			

if __name__ == "__main__":        
	webServer = HTTPServer((hostName, serverPort), MyServer)
	#webServer.socket = ssl.wrap_socket (webServer.socket, certfile='./server.pem', server_side=True)

	print("Server started %s:%s" % (hostName, serverPort))
	
	try:
		webServer.serve_forever()
	except KeyboardInterrupt:
		pass

	webServer.server_close()
	print("Server stopped.")
