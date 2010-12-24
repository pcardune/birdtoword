var
  path = require('path'),
  fs = require('fs'),
  _ = require('underscore');

var BASE_BUCKET_PATH = path.join(__dirname, '../app/src/birdtoword/data');

/**
 * Helper function to pick a random item from an array,
 * or a random key from an object.
 */
function _choice(data) {
  var keys = _.keys(data);
  var i = Math.floor(Math.random() * keys.length);
  return _.isArray(data) ? data[keys[i]] : keys[i];
}

function Bucket(data) {
  this.data = data;
}

Bucket.prototype = {
  getPath: function() {
    var wordPath = null;
    var count = 0;
    while (wordPath == null) {
      count++;
      var fromWord = _choice(this.data);
      wordPath = [fromWord];
      var segments = Math.floor(Math.random()*15) + 5;
      var toWord = fromWord;
      while (wordPath.length < segments) {
        var possible = this.data[toWord]
          .filter(function(w){
            return wordPath.indexOf(w) < 0;
          });
        if (!possible.length) {
          wordPath = null;
          break;
        }
        toWord = _choice(possible);
        wordPath.push(toWord);
      }
    }
    return {'from':_.first(wordPath), 'to':_.last(wordPath)};
  }
};

function LazyBuckets() {
  this.data = {};
  this._keys = fs.readdirSync(BASE_BUCKET_PATH)
    .filter(function(f) {
      return f.indexOf('.dat.json.') > 0;
    })
    .map(function(f) {
      return parseInt(f.split('.').pop());
    });
}

LazyBuckets.prototype = {

  getFilePath: function(size) {
    return path.join(BASE_BUCKET_PATH, 'buckets.dat.json.'+size);
  },

  getBucket: function(size, callback) {
    if (this.data.hasOwnProperty(size)) {
      callback(this.data[size]);
    } else if (this._keys.indexOf(size) >= 0) {
      fs.readFile(this.getFilePath(size), _.bind(function(err, data) {
        if (err) {
          throw err;
        }
        this.data[size] = new Bucket(JSON.parse(data));
        callback(this.data[size]);
      }, this));
    } else {
      throw new Error("No bucket for size "+size);
    }
  }
};

exports.BUCKETS = new LazyBuckets();