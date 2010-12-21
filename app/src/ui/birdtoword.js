// borrowed from John Resig's blog post: http://ejohn.org/blog/simple-javascript-inheritance/
// Inspired by base2 and Prototype
(function(){
  var initializing = false, fnTest = /xyz/.test(function(){xyz;}) ? /\b_super\b/ : /.*/;

  // The base Class implementation (does nothing)
  this.Class = function(){};

  // Create a new Class that inherits from this class
  Class.extend = function(prop) {
    var _super = this.prototype;

    // Instantiate a base class (but only create the instance,
    // don't run the init constructor)
    initializing = true;
    var prototype = new this();
    initializing = false;

    // Copy the properties over onto the new prototype
    for (var name in prop) {
      // Check if we're overwriting an existing function
      prototype[name] = typeof prop[name] == "function" &&
        typeof _super[name] == "function" && fnTest.test(prop[name]) ?
        (function(name, fn){
          return function() {
            var tmp = this._super;

            // Add a new ._super() method that is the same method
            // but on the super-class
            this._super = _super[name];

            // The method only need to be bound temporarily, so we
            // remove it when we're done executing
            var ret = fn.apply(this, arguments);
            this._super = tmp;

            return ret;
          };
        })(name, prop[name]) :
        prop[name];
    }

    // The dummy class constructor
    function Class() {
      // All construction is actually done in the init method
      if ( !initializing && this.init )
        this.init.apply(this, arguments);
    }

    // Populate our constructed prototype object
    Class.prototype = prototype;

    // Enforce the constructor to be what we expect
    Class.constructor = Class;

    // And make this class extendable
    Class.extend = arguments.callee;

    return Class;
  };
})();


////here is an example for using the above code.
//var Person = Class.extend({
//  init: function(isDancing){
//    this.dancing = isDancing;
//  },
//  dance: function(){
//    return this.dancing;
//  }
//});
//
//var Ninja = Person.extend({
//  init: function(){
//    this._super( false );
//  },
//  dance: function(){
//    // Call the inherited version of dance()
//    return this._super();
//  },
//  swingSword: function(){
//    return true;
//  }
//});


/**
 * @namespace birdtoword namespace
 */
var birdtoword = {};

(function($){


birdtoword.Dictionary = Class.extend(
    {
        words: [],

        init: function(config){
            this.words = config.words;
        },

        contains: function(word){
            for (var i=0; i < this.words.length; i++){
                if (this.words[i] === word){
                    return true;
                }
            }
            return false;
        }
    });

birdtoword.GameEntry = Class.extend(
    {
        el: null,
        active: false,
        startTime: null,
        endTime: null,
        init: function(config){
            this.originalWord = config.word;
            this.word = config.word;
            this.game = config.game;
            this.startTime = new Date();
            this._render();
            this.startTimer();
            this.connected = null;
        },

        focus: function(){
            $(this.el).find("input:first").focus();
        },

        getKeyPressHandler: function(charIndex){
            var entry = this;
            var game = this.game;
            function handleKeyPress(event){
                if (event.originalEvent.keyCode === 37){
                    // left arrow key
                    $(this).prev().focus();
                } else if (event.originalEvent.keyCode === 39){
                    // right arrow key
                    $(this).next().focus();
                }
                if (event.which >= 32 && event.which <= 127){
                    entry.word = entry.word.slice(0,charIndex)+String.fromCharCode(event.which)+entry.word.slice(charIndex+1);
                    if (entry.word === entry.originalWord){
                        $(entry.el).find("input").removeClass("fail").removeClass("ok");
                    } else if (entry.connected.contains(entry.word)){
                        entry.finish();
                        if (entry.word === game.to){
                            game.win();
                        } else {
                            $(entry.el).find("input").removeClass("fail").addClass("ok");
                            game.newEntry(entry.word);
                        }
                    } else {
                        $(entry.el).find("input").addClass("fail").removeClass("ok");
                    }
                    $(this).val("");
                }
                return true;
            }
            return handleKeyPress;
        },

        getTime: function(){
            var endTime = this.endTime || new Date();
            return (endTime.getTime()-this.startTime.getTime())/1000;
        },

        update: function(){
            if (this.rendered){
                $(this.timerEl).html(""+Math.round(this.getTime()));
            }
        },

        startTimer: function(){
            var entry = this;
            this.timer = window.setInterval(function(){entry.update();}, 1000);
        },

        finish: function(){
            this.stopTimer();
            var entry = this;
            $("<a class=\"please-define\">WTF?</a>")
                .click(birdtoword.getDefinitionClickHander(this.word))
                .appendTo(this.el);
            $(this.el).addClass("fixed-word");
            window.setTimeout(function(){entry.disable();}, 100);
        },

        stopTimer: function(){
            this.endTime = new Date();
            $(this.timerEl).html(Math.round(this.getTime()*10)/10);
            window.clearInterval(this.timer);
        },

        disable: function(){
            $(this.el).find("input").attr("disabled","disabled");
        },

        _render: function(){
            var gameEntry = this;
            if (this.connected == null){
                $.getJSON(
                    '/api/words/'+this.word+'/connected',
                    function(connected){
                        gameEntry.connected = new birdtoword.Dictionary({words:connected});
                        gameEntry._render();
                    });
                return;
            }
            this.el = $("<div class=\"entry\"></div>")
                .appendTo(this.game.getEntryContainer()).get(0);

            for (var i=0; i < this.word.length; i++){
                $('<input type="text" value="'+this.word[i]+'"/>')
                    .appendTo(this.el)
                    .keypress(this.getKeyPressHandler(i));
            }

            this.timerEl = $("<span class=\"timer\"></span>")
                .html(this.getTime())
                .appendTo(this.el)
                .get();
            this.focus();
            this.rendered = true;
        }
    });

birdtoword.sendChallengeEmail = function(data, callback){
    $.post("/api/challenge/email", data, callback, "json");
};

birdtoword.getWordDefinitionHtml = function(word, callback){
    $.getJSON(
        "/api/words/"+word+"/definition",
        function(data){
            var html;
            if (typeof(data) === "object"){
                html = "<ul>";
                for (type in data){
                    html += "<li>("+type+")<ol>";
                    for (var i=0; i<data[type].length; i++){
                        html += "<li>"+data[type][i]+"</li>";
                    }
                    html += "</ol></li>";
                }
                html += "</ul>";
            } else {
                html = "<div>"+data+"</div>";
            }
            callback(html);
        });
};

birdtoword.getDefinitionClickHander = function(word){
    return function(){
        $("#definition-wrapper")
            .show()
            .find(".definition")
            .html("Getting the definition for "+word);
        birdtoword.getWordDefinitionHtml(
            word,
            function(html){
                $("#definition-wrapper")
                    .show()
                    .find(".definition")
                    .html("<strong>"+word+"</strong>"+html);
            });
    };
};

birdtoword.Game = Class.extend(
    {
        _rendered: false,
        dictionary: new birdtoword.Dictionary({words:['word','bird','ward','bard']}),
        startTime: null,
        endTime: null,
        wordLength: 3,
        init: function(config){
            this.containerId = config.el;
            this.el = null;
            if (config.from.length != config.to.length){
                throw new Error("From and To words must be the same length!");
            }
            this.from = config.from;
            this.to = config.to;
            this.entries = [];
            if (config.autoShow){
                this.show();
            }
            this.getNextGameWords();
        },

        getNextGameWords: function(callback){
            var game = this;
            game.nextGame = {};
            $.getJSON(
                '/api/game-words/'+this.wordLength,
                function(words){
                    game.nextGame.from = words.from;
                    game.nextGame.to = words.to;
                    if (callback) callback(words);
                });
        },

        getEntryContainer: function(){
            return $(this.el).find(".entries");
        },

        getEntryCount: function(){
            return $(this.el).find(".entry").length;
        },

        getEntryAt: function(index){
            var word = "";
            $(this.el).find(".entry").eq(index)
                .find("input").each(function(){word += $(this).val();});
            return word;
        },

        newEntry: function(word){
            var newEntry = new birdtoword.GameEntry(
                {
                    game: this,
                    word: word
                });
            this.entries.push(newEntry);
            newEntry.focus();
        },

        reset: function (){
            this.from = this.nextGame.from;
            this.to = this.nextGame.to;
            this.getNextGameWords();
            while (this.entries.length > 0){
                this.entries.pop();
            }
            this._rendered = false;
            this.show();
        },

        _render: function(){
            // clear out anything that is there.
            this.el = $("#templates .game").clone()
                .appendTo($(document.getElementById(this.containerId)).html("")).get(0);

            var el = $(this.el);
            var fromEl = el.find('.from-word');
            var toEl = el.find('.to-word');

            el.find(".levels span").eq(this.wordLength-3).addClass("selected");
            fromEl.append("<label>From:</label>");
            toEl.append("<label>To:</label>");
            for (var i=0; i<this.from.length; i++){
                fromEl.append("<span class=\"char\">"+this.from[i]+"</span>");
                toEl.append("<span class=\"char\">"+this.to[i]+"</span>");
            }
            toEl.append("<span class=\"time\"></span>");
            $("<a class=\"please-define\">WTF?</a>")
                .click(birdtoword.getDefinitionClickHander(this.from))
                .appendTo(fromEl);
            $("<a class=\"please-define\">WTF?</a>")
                .click(birdtoword.getDefinitionClickHander(this.to))
                .appendTo(toEl);

            var game = this;
            function resetHandler(){
                game.reset();
            };
            function levelClickHandler(){
                game.wordLength = parseInt($(this).text()[0]);
                game.getNextGameWords(function(){game.reset();});
            }
            function shareOnFacebook(){
                FB_RequireFeatures(
                    ["Api"],
                    function(){
                        FB.Connect.showFeedDialog(
                            90839420818,
                            {fromWord:game.from, toWord:game.to, steps:game.entries.length},
                            [],
                            "",
                            null,
                            FB.RequireConnect.promptConnect
                        );
                    });
            }
            function challengeFriend(){
                $("#challenge-friend").dialog("open");
            }
            $(this.el)
                .find(".play-again button").click(resetHandler).end()
                .find(".share-fb button").click(shareOnFacebook).end()
                .find(".challenge button").click(challengeFriend).end()
                .find(".too-hard-button").click(resetHandler).show().end()
                .find(".levels span").click(levelClickHandler).end();
            this.newEntry(this.from);
            this._rendered = true;
        },

        show: function(){
            this.startTime = new Date();
            if (!this._rendered){
                this._render();
            }
            $(this.el).show();
        },

        win: function(){
            var data = {words:[this.from], times: []};
            var totalTime = 0;
            for (var i=0; i < this.entries.length; i++){
                var entry = this.entries[i];
                data.words.push(entry.word);
                data.times.push(entry.getTime());
                totalTime += entry.getTime();
            }
            var roundedTime = Math.round(totalTime*10)/10;
            $(this.el)
                .find(".to-word .time").html(roundedTime).end()
                .find(".win").html("You made it in "+roundedTime+" seconds with "+this.entries.length+" transformations").show().end()
                .find(".play-again")
                    .find("button").click(function(){}).end()
                .show().focus().end()
                .find(".share-fb")
                    .find("button").click(function(){}).end()
                .show().end()
                .find(".challenge")
                    .find("button").click(function(){}).end()
                .show().end()
                .find(".too-hard-button").hide().end();


            $.post(
                '/api/save-game',
                data,
                function(data){
                    $("#game-history .table-wrapper tr:last").clone()
                        .find(".from").html(data.fromWord).end()
                        .find(".to").html(data.toWord).end()
                        .find(".time").html(data.time).end()
                        .find(".changes").html(data.changes).end()
                        .addClass("new")
                        .insertBefore("#game-history .table-wrapper table tr:first")
                        .show();

                },"json");
        }
    });

birdtoword.WordExplorerPage = Class.extend(
    {
        _rendered: false,
        init: function(config){
            this.el = document.getElementById(config.el);
            this.word = config.word;
            this.wordExplorer = config.wordExplorer;
            this.connected = [];
        },

        _render: function(){
            var page = this;

            if (this.connected.length == 0){
                $.getJSON(
                    '/api/words/'+this.word+'/connected',
                    function(data){
                        page.connected = data;
                        page._render();
                    }
                );
                return;
            }
            $(this.el).append("<h1>"+this.word+"</h1>");
            var wordsEl = $("<ul></ul>").appendTo(this.el);
            for (var i=0; i < this.connected.length; i++){
                var wordHtml = "";
                var j=0;
                for (j=0; j < this.connected[i].length; j++){
                    var c = this.connected[i][j];
                    if (this.word[j] === c){
                        wordHtml += c;
                    } else {
                        wordHtml += '<em>'+c+'</em>';
                    }
                }

                $("<li></li>")
                    .html(wordHtml)
                    .appendTo(wordsEl)
                    .click(
                        function(){
                            $(page.el).nextAll().remove();
                            page.wordExplorer.newPage($(this).text());
                            $(this).addClass('selected').siblings().removeClass('selected');

                        });
            }
        },

        show: function(){
            if (!this._rendered){
                this._render();
            }
            $(this.el).show();
        }

    });

birdtoword.WordExplorer = Class.extend(
    {
        _rendered: false,
        init: function(config){
            this.el = document.getElementById(config.el);
            this.from = config.from;
            this.pages = [];
            if (config.autoShow){
                this.show();
            }
        },


        newPage: function(word){
            for (var i=0; i < this.pages.length; i++){
                if (this.pages[i].word === word){
                    $(this.pages[i].el).nextAll().remove();
                    this.pages = this.pages.slice(0,i);
                    return;
                }
            }
            var pageId = $(this.el).attr('id')+'-'+word+'-'+$(this.el).find(".explorer-page").length;
            $(this.el).append('<div id="'+pageId+'" class="explorer-page"></div>');
            var page = new birdtoword.WordExplorerPage(
                {
                    el:pageId,
                    word: word,
                    wordExplorer: this
                });
            this.pages.push(page);
            page.show();
        },

        _render: function(){
            this.newPage(this.from);
        },

        show: function(){
            if (!this._rendered){
                this._render();
            }
            $(this.el).show();
        }

    });




})(jQuery);