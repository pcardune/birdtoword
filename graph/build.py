import sys
import os
import re
import random
import optparse
import logging
import simplejson
from birdtoword.graph import Node, Bucket

logger = logging.getLogger('info')
random = random.Random('seed')

parser = optparse.OptionParser(usage="%prog [-c]")

parser.add_option(
    "-c", "--compile", action="store",
    dest="compile", metavar="DIR",
    help="Compile word lists in the given directory into their similarity graph.")

parser.add_option(
    "-e", "--explore", action="store",
    dest="exploreFile", metavar="FILE",
    help="Explore the similarity graph defined in the given file.")

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
    "-q","--quiet", action="store_true",
    dest="quiet", default=False,
    help="When specified, no messages are displayed.")

parser.add_option(
    "-v","--verbose", action="store_true",
    dest="verbose", default=False,
    help="When specified, debug information is created.")


def runCompile(options):
    #set up max size option
    try:
        maxSize = int(options.maxSize)
        logger.info("maxsize: %i" % maxSize)
    except ValueError, e:
        logger.error("max-size must be an integer: %s" % e)
        sys.exit(1)

    #set up file paths
    dataDir = os.path.abspath(options.compile)
    outputFile = os.path.abspath(options.outputFile)
    logger.info("Compiling wordlists from %s to %s" % (options.compile, options.outputFile))


    wordRegex = re.compile("^[a-z]*$")
    words = []
    for filename in os.listdir(dataDir):
        filepath = os.path.join(dataDir, filename)
        words += [line[:-1]
                  for line in open(filepath, 'r').readlines()
                  if wordRegex.match(line[:-1])]
    words.sort()
    buckets = {}
    for wordIndex in xrange(len(words)):
        word = words[wordIndex]
        length = len(word)
        buckets.setdefault(length, Bucket(length))
        buckets[length].append(word)
    output = ""
    for length in xrange(2, maxSize+1):
        bucketNodes = buckets.get(length, Bucket(length))
        logger.info("processing %s words of length %s" % (len(bucketNodes), length))

        totalConnections = 0
        for node in bucketNodes:
            for otherNode in bucketNodes:
                node.append(otherNode)
            totalConnections += len(node)

        output += bucketNodes.export()

        logger.info("%s connections between %s words" % (totalConnections, len(bucketNodes)))

    open(outputFile,'w').write(output)
    logger.info("Wrote %s" % outputFile)

def runExplore(options):
    inputFile = os.path.abspath(options.exploreFile)
    lines = open(inputFile).readlines()
    buckets = {}
    lineIndex = 0
    while lineIndex < len(lines):
        line = lines[lineIndex][:-1]
        tokens = line.split(' ')
        if tokens[0] == "b":
            wordCount = int(tokens[1])
            wordSize = int(tokens[2])
            bucket = Bucket(wordSize)
            wordLineTokens = [lines[lineIndex+lineOffset][:-1].split(' ')
                              for lineOffset in xrange(1, wordCount+1)]
            for wordLine in wordLineTokens:
                bucket.append(wordLine[1])
            for wordLine in wordLineTokens:
                wordIndex = int(wordLine[0])
                for connectedId in wordLine[2:]:
                    if not connectedId: continue
                    connectedIndex = int(connectedId)
                    bucket[wordIndex].append(bucket[connectedIndex])
            lineIndex += wordCount
            buckets[wordSize] = bucket
        else:
            lineIndex += 1
    print "Pick a word size to explore:"
    for key in buckets:
        print "  ",key,"-", len(buckets[key]), "words"
    wordSize = int(raw_input("word size: "))
    bucket = buckets[wordSize]
    print " ".join([n.word for n in bucket])
    while True:
        word = raw_input("word: ")
        node = bucket.find(word)
        print " ".join([n.word for n in node])


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

    if options.compile:
        runCompile(options)
    if options.exploreFile:
        runExplore(options)

if __name__ == '__main__':
    main()
