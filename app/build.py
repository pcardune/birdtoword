import simplejson
import cjson
import pickle
import sys
import os
import re
import random
import optparse
import logging
import paths_pb2
import csv

logger = logging.getLogger('info')
random = random.Random('seed')

parser = optparse.OptionParser(usage="%prog [-c]")

parser.add_option(
    "-c", "--compile", action="store",
    dest="compile", metavar="DIR",
    default="/usr/share/dict/words",
    help="Compile word lists in the given directory into their similarity graph.")

parser.add_option(
    "-o", "--output-file", action="store",
    dest="outputFile", metavar="FILE",
    default="words.txt",
    help="Compile word lists in the given directory into their similarity graph.")

parser.add_option(
    "-s", "--max-size", action="store",
    dest="maxSize", metavar="MAXSIZE",
    default="3",
    help="The maximum number of letters in a word to compile.")

parser.add_option(
    "-m", "--min-size", action="store",
    dest="minSize", metavar="MINSIZE",
    default="3",
    help="The minimum number of letters in a word to compile.")

parser.add_option(
    "-q","--quiet", action="store_true",
    dest="quiet", default=False,
    help="When specified, no messages are displayed.")

parser.add_option(
    "-v","--verbose", action="store_true",
    dest="verbose", default=False,
    help="When specified, debug information is created.")

parser.add_option(
    "-t","--to-csv", action="store",
    dest="csv", default=False,
    help="The file from which to generate a csv")

INFINITY = 999999999999

class _Word(object):
    counter = 0
    byWord = {}

    def __init__(self, word):
        self.word = word
        self.id = _Word.counter
        _Word.counter += 1
        _Word.byWord[self.word] = self

    def __repr__(self):
        return "{%s}" % self.word

def Word(word):
    if _Word.byWord.has_key(word):
        return _Word.byWord[word]
    return _Word(word)

class Node(object):
    def __init__(self, word):
        self.word = Word(word)
        self.connected = set()
        self.parent = None
        self.distance = INFINITY

    def __repr__(self):
        return "<%s>" % self.word

def buildNodeSetFromBucket(bucket, findWord=None):
    nodeDict = {}
    for word in bucket.keys():
        nodeDict[word] = Node(word)
    for node in nodeDict.values():
        connectedNodes = [nodeDict[otherWord] for otherWord in bucket[node.word.word]]
        node.connected = node.connected.union(connectedNodes)
    if findWord is not None:
        return set(nodeDict.values()), nodeDict[findWord]
    return set(nodeDict.values())

def connected(word1, word2):
    if len(word1) != len(word2):
        return False
    offset = 0
    for i in xrange(len(word1)):
        if word1[i] != word2[i]:
            offset += 1
        if offset > 1:
            return False
    if offset == 1:
        return True
    return False

def inverted(d):
    """Switches keys and values in a dictionary.

    so you can look up by value and get a list of keys.
    """
    newD = {}
    for key, val in d.items():
        if not newD.has_key(val):
            newD[val] = []
        newD[val].append(key)
    return newD

def getDistanceMapForWord(word, bucket):
    """Get the distance map using dijkstras algorithm."""
    allNodes, currentNode = buildNodeSetFromBucket(bucket, findWord=word)
    currentNode.distance = 0
    nodes = set([n for n in allNodes]) # make a copy
    while len(nodes) > 0:
        nearestNode = min(nodes, key=lambda n: n.distance)
        if nearestNode.distance == INFINITY:
            break
        nodes.remove(nearestNode)
        for connectedNode in nearestNode.connected.intersection(nodes):
            alternativeDist = nearestNode.distance+1 # distance between two connected nodes is 1
            if alternativeDist < connectedNode.distance:
                connectedNode.distance = alternativeDist
                connectedNode.parent = nearestNode
    return allNodes, currentNode

def getShortestPathsForWord(word, bucket):
    nodes, wordNode = getDistanceMapForWord(word, bucket)

    def getPathKey(n1, n2):
        if n1.word <= n2.word:
            return (n1, n2)
        else:
            return (n2, n1)

    paths = {}
    for node in nodes:
        pathKeys = set()
        currentNode = node
        while currentNode.parent != None:
            key = getPathKey(wordNode, currentNode)
            if paths.has_key(key):
                for pathKey in pathKeys:
                    paths[pathKey] += paths[key]
                break
            else:
                pathKeys.add(key)
                paths[key] = []
                for pathKey in pathKeys:
                    paths[pathKey].append(currentNode)
            currentNode = currentNode.parent
        for pathKey in pathKeys:
            if paths[pathKey][-1] != wordNode:
                paths[pathKey].append(wordNode)
    for key, path in paths.items():
        if key[0] != path[0].word:
            path.reverse()
        # this transformation causes a lot of memory to be used
        paths[key] = [n.word for n in path]
    return paths.values()

def getShortestPathsForBucket(bucket):
    paths = []
    char = "a"
    logger.info("processing words starting with %s (%i/%i)" % (char, 0, len(bucket)))
    count = 0
    for word in sorted(bucket.keys()):
        count += 1
        if word[0] != char:
            char = word[0]
            logger.info("processing words starting with %s (%i/%i)" % (char, count, len(bucket)))
        paths += getShortestPathsForWord(word, bucket)
    return paths

## def runDistanceComputation(outputFile, buckets):
##     byDistanceMaps = {}
##     dmaps = {}
##     for size, bucket in buckets.items():
##         dmaps[size], byDistanceMaps[size] = getShortestPathsForBucket(bucket)

##         logger.info("finished compiling distance maps for size %i" % size)
##         fn = "%s.dmap.json.%i" % (outputFile, size)
##         logger.info("Writing %s" % fn)
##         open(fn,'w').write(simplejson.dumps(dmaps[size]))

##         fn = "%s.rmap.json.%i" % (outputFile, size)
##         logger.info("Writing %s" % fn)
##         open(fn,'w').write(simplejson.dumps(byDistanceMaps[size]))

def getWordListFromFile(f):
    wordRegex = re.compile("^[a-z]+$")
    if not isinstance(f, file):
        f = open(f)
    return [line.strip()
            for line in f.readlines()
            if wordRegex.match(line.strip())]

def getBucketFromWordList(words, size):
    bucket = {}
    words = [w for w in words if len(w) == size]
    for word in words:
        bucket[word] = []
    for word in bucket:
        bucket[word] = [otherWord for otherWord in bucket if connected(word, otherWord)]
    return bucket

def serializePathsForBucket(pathsForBucket):
    """Turn node paths into plain python objects for serialization."""
    allWords = set()

    pathFile = paths_pb2.PathFile()
    for path in pathsForBucket:
        allWords.update(path)
        pathPb = pathFile.paths.add()
        for p in path:
            pathPb.wordReferences.append(p.id)
    for w in allWords:
        wordPb = pathFile.words.add()
        wordPb.id = w.id
        wordPb.word = w.word
    return pathFile

def runCompile(options):
    #set up min size option
    minSize = int(options.minSize)
    maxSize = int(options.maxSize)

    #set up file paths
    wordFile = os.path.abspath(options.compile)
    outputFile = os.path.abspath(options.outputFile)
    logger.info("Compiling wordlists from %s to %s" % (options.compile, options.outputFile))

    words = getWordListFromFile(wordFile)
    logger.info("Processing a total of %i words" % len(words))

    buckets = {}
    for size in xrange(minSize, maxSize+1):
        bucket = getBucketFromWordList(words, size)
        logger.info("Compiling shortest paths between %i %i letter words" % (len(bucket), size))
        pathsForBucket = getShortestPathsForBucket(bucket)

        serialized = serializePathsForBucket(pathsForBucket)
        fn = "%s.protobuf.%i" % (outputFile, size)
        logger.info("Writing %s" % fn)
        open(fn,'w').write(serialized.SerializeToString())

def runConvertToCsv(options):
    logger.info("opening %s" % options.csv)
    pathFile = paths_pb2.PathFile()
    data = open(options.csv).read()
    logger.info("deserializing %s" % options.csv)
    pathFile.ParseFromString(data)
    logger.info("building word dictionary from %s" % options.csv)
    words = dict([(w.id,w.word) for w in pathFile.words])
    rows = set()
    logger.info("converting %s to csv" % options.csv)
    for path in pathFile.paths:
        key = sorted((words[path.wordReferences[0]], words[path.wordReferences[-1]]))
        rows.add(tuple(key+[len(path.wordReferences)]))

    logger.info("Writing %s.csv" % options.csv)
    outFile = open(options.csv+'.csv', 'w')
    writer = csv.writer(outFile)
    writer.writerows(rows)
    outFile.close()
    logger.info("Done!")

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    if not args:
        args = ['-h']

    # Parse arguments
    options, args = parser.parse_args(args)

    # Set up logger handler
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    if options.verbose:
        logger.setLevel(logging.DEBUG)
    if options.quiet:
        logger.setLevel(logging.FATAL)

    if options.csv:
        runConvertToCsv(options)
    elif options.compile:
        runCompile(options)

if __name__ == '__main__':
    main()
