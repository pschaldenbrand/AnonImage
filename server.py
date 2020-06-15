import http.server
import socketserver
import cv2
import numpy as np
import cgi
import base64

from anonymize_image import *

PORT = 8081

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):            
        possible_name = self.path.strip("/")+'.html'
        if self.path == '/':
            self.path = '/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    def do_POST(self):
        if self.path == '/anonymize_image':
            # From https://fragments.turtlemeat.com/pythonwebserver.php
            ctype, pdict = cgi.parse_header(self.headers['content-type'])

            if 'boundary' in pdict.keys():
                # From https://stackoverflow.com/questions/31486618/cgi-parse-multipart-function-throws-typeerror-in-python-3
                pdict['boundary'] = bytes(pdict['boundary'], "utf-8") 

            if ctype == 'multipart/form-data':
                query=cgi.parse_multipart(self.rfile, pdict)

            img_content = query.get('image')
            nparr = np.fromstring(img_content[0], np.uint8)
            uploaded_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            

            img = anonymize_image(uploaded_img)
            img_str = cv2.imencode('.jpg', img)[1].tostring()
            img_bytes = base64.b64encode(img_str)

            # From https://stackabuse.com/serving-files-with-pythons-simplehttpserver-module/
            self.send_response(200)
            self.send_header("Content-type", "image/jpeg")
            # self.send_header("Content-Type", 'application/octet-stream')
            # self.send_header("Content-Disposition", 'attachment; filename="{}"'.format(os.path.basename(FILEPATH)))
            # self.send_header("Content-Disposition", 'attachment; filename="anonymized.jpg"')
            self.send_header("Content-Length", len(img_bytes))
            self.end_headers()

            self.wfile.write(img_bytes)

Handler = MyRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()