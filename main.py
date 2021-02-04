from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from string import Template
import time, json, requests, math, sys

hostName = "0.0.0.0"
port = int(sys.argv[1])

headers = {}

f = open("index.html", "r")
rawHtml = f.read()
f.close()
indexTemplate = Template(rawHtml)

f = open("search.html", "r")
rawHtml = f.read()
f.close()
searchTemplate = Template(rawHtml)

class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        username = ""
        hours = 0
        userParam = ""
        search = ""
        error = ""
        if 'steam_id' in query:
            userParam = "steam_id="+query.get('steam_id')[0]
        if 'profile_id' in query:
            userParam = "profile_id="+query.get('profile_id')[0]
        if 'search' in query:
            search = query.get('search')[0]
        if len(search) > 0:
                responseSearch = requests.get("http://aoe2.net/leaderboard/aoe2de/rm-team?search%5Bregex%5D=false&search%5Bvalue%5D="+search, verify=False, headers=headers)
                result = responseSearch.json()['data']
                if len(result)>0:
                    user = result[0]
                    if user['profile_id']:
                        userParam = "profile_id="+str(user['profile_id'])
                    else:
                        if user['steam_id']:
                            userParam = "steam_id="+str(user['steam_id'])
                else:
                    error = "User not found"
        if len(userParam)>0:
            responseLastMatch = requests.get("http://aoe2.net/api/player/lastmatch?game=aoe2de&"+userParam, verify=False, headers=headers)
            if responseLastMatch.status_code == 200:
                lastmatch = responseLastMatch.json()
                username = lastmatch['name']
            responseHistory = requests.get("http://aoe2.net/api/player/matches?game=aoe2de&count=9999999&"+userParam, verify=False, headers=headers)
            if responseHistory.status_code == 200:
                history = responseHistory.json()
                time = 0
                for match in history:
                    if match['finished'] and match['started']:
                        time = time + match['finished']-match['started']
                hours = math.ceil(time / (60 * 60))
            if len(username) > 0 and hours > 0:
                html = indexTemplate.substitute(name=username, hours=hours)
            else:
                html = searchTemplate.substitute(error=error)
        else:
            html = searchTemplate.substitute(error=error)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes(html, "utf-8"))

if __name__ == "__main__":        
    webServer = HTTPServer((hostName, port), Server)
    print("Server started http://%s:%s" % (hostName, port))
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
    print("Server stopped.")