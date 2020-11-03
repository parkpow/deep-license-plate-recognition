import cgi
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from json.decoder import JSONDecodeError


class GetHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Send a POST request instead.')
        return

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
        if ctype == 'multipart/form-data':
            pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
            fields = cgi.parse_multipart(self.rfile, pdict)
            # Get webhook content
            json_data = json.loads(fields.get('json')[0])
            buffer = fields.get('upload')[0]
            name = 'new_image.jpg'
            print('Saving image to %s' % name)
            with open(name, 'wb') as fp:
                fp.write(buffer)
        else:
            raw_data = self.rfile.read(int(
                self.headers['content-length'])).decode('utf-8')
            if raw_data.startswith('json='):
                raw_data = raw_data[5:]
            try:
                json_data = json.loads(raw_data)
            except JSONDecodeError:
                json_data = {}
        print(json_data)
        self.wfile.write(b'OK')


if __name__ == '__main__':
    server = HTTPServer(('', 8001), GetHandler)
    print('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()
