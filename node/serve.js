var express = require('express');
var jade = require('jade');

var app = express.createServer(
    express.logger(),
    express.bodyDecoder()
);

app.configure(
    function(){
        app.use(express.cookieDecoder());
        app.use(express.session());
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

console.log("running on port 3000");
app.listen(3000);