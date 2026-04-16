const http = require('http');
const fs = require('fs');
const path = require('path');
const PORT = 8765;
const ROOT = __dirname;
const MIME = {'.html':'text/html','.css':'text/css','.js':'application/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.ico':'image/x-icon'};

http.createServer((req, res) => {
  let url = decodeURI(req.url.split('?')[0]);
  if (url === '/') url = '/index.html';
  const file = path.join(ROOT, url);
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); res.end('404'); return; }
    const ext = path.extname(file).toLowerCase();
    res.writeHead(200, {'Content-Type': MIME[ext] || 'text/plain'});
    res.end(data);
  });
}).listen(PORT, () => console.log('serving on :' + PORT));
