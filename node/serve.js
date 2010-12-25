var
  express = require('express'),
  jade = require('jade'),
  MemoryStore = require('connect/middleware/session/memory'),
  _ = require('underscore'),
  graph = require('./graph.js');

var app = express.createServer(
  express.logger(),
  express.bodyDecoder()
);

app.configure(
  function(){
    app.use(express.cookieDecoder());
    app.use(express.session({store:new MemoryStore({reapInterval: 60000 * 10 })}));
    app.use(express.methodOverride());
    app.use(express.bodyDecoder());
    app.use(app.router);
    app.use(express.staticProvider(__dirname + '/../app/src/ui'));
  });

app.configure(
  'development',
  function(){
    app.use(express.errorHandler({ dumpExceptions: true, showStack: true }));
  });

app.configure(
  'production',
  function(){
    app.use(express.errorHandler());
  });

app.set('view engine', 'jade');

app.get(
  '/',
  function(req, res) {
    res.render('index', {
                 locals: {scripts: ['front-page.js']}
               });
  });

app.get(
  /\/api\/game-words\/([345])/,
  function(req, res) {
    var size = parseInt(req.params[0]);
    graph.getBucket(size, function(bucket) {
      res.send(bucket.getPath());
    });
  });

app.get(/\/api\/words\/(.*)\/connected/, function(req, res) {
  var word = req.params[0];
  graph.getBucket(word.length, function(bucket) {
    res.send(bucket.getConnected(word));
  });
});

app.post('/api/save-game', function(req, res) {
  var
    words = req.param("words"),
    times = req.param("times");

  if (!req.session.games) {
    req.session.games = [];
  }

  req.session.games.push({
    fromWord: words[0],
    toWord: _.last(words),
    words: words.slice(1, words.length-1),
    times: [times.map(function(t){ return parseFloat(t); })]
  });

  res.send(null);
});

var port = 3000;
console.log("running on port", port);
app.listen(port);