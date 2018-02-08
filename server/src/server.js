// Simple web server for putting a Python REPL in a client's browser.

var express = require('express');
var app = express();
var expressWs = require('express-ws')(app);
var os = require('os');
var pty = require('node-pty');

var repls = {},
    logs = {};

app.use('/build', express.static(__dirname + '/../build'));

app.get('/', function(req, res){
  res.sendFile(__dirname + '/index.html');
});

// Create a new REPL
app.post('/repls', function (req, res) {
  var cols = parseInt(req.query.cols),
      rows = parseInt(req.query.rows),
      repl = pty.spawn(
          'python', [], {
              name: 'xterm-color',  // Sets the TERM environment variable, so
                                    // must be 'xterm' or 'xterm-color'
              cols: cols || 80,
              rows: rows || 24,
              cwd: process.env.PWD,
              env: process.env
          });

  console.log('Created Python REPL with PID: ' + repl.pid);
  repls[repl.pid] = repl;
  logs[repl.pid] = '';
  repl.on('data', function(data) {
    logs[repl.pid] += data;
  });
  res.send(repl.pid.toString());
  res.end();
});

// Resize a repl
app.post('/repls/:pid/size', function (req, res) {
  var pid = parseInt(req.params.pid),
      cols = parseInt(req.query.cols),
      rows = parseInt(req.query.rows),
      repl = repls[pid];

  repl.resize(cols, rows);
  console.log('Resized terminal ' + pid + ' to ' + cols + ' cols and ' + rows + ' rows.');
  res.end();
});

// Websocket for interacting with REPL
app.ws('/repls/:pid', function (ws, req) {
  var repl = repls[parseInt(req.params.pid)];
  console.log('Connected to terminal ' + repl.pid);
  ws.send(logs[repl.pid]);

  repl.on('data', function(data) {
    try {
      ws.send(data);
    } catch (ex) {
      // The WebSocket is not open, ignore
    }
  });
  ws.on('message', function(msg) {
    repl.write(msg);
  });
  ws.on('close', function () {
    repl.kill();
    console.log('Closed terminal ' + repl.pid);
    // Clean things up
    delete repls[repl.pid];
    delete logs[repl.pid];
  });
});

var port = process.env.PORT || 3000,
    host = os.platform() === 'win32' ? '127.0.0.1' : '0.0.0.0';

console.log('App listening to http://' + host + ':' + port);
app.listen(port, host);
