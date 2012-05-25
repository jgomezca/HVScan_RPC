#!/usr/bin/env python2.6
'''Generates the docs for CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


defaultOutputDirectory = 'generated'
docsFilename = 'docs.css'
indexFilename = 'index.html'

indexTitle = 'Docs\' Index'

docsTemplate = '''
	<html>
		<head>
			<title>%s</title>
			<link rel="stylesheet" type="text/css" href="%s" />
		</head>
		<body>
			%s
		</body>
	</html>
'''


import os
import shutil
import re
import markdown
import optparse
import logging
logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO
)
logger = logging.getLogger(__name__)


def getOptions():
	'''Parses the arguments from the command line.
	'''

	parser = optparse.OptionParser()

	parser.add_option('-o', '--outputDirectory', type='str',
		dest='outputDirectory',
		default=defaultOutputDirectory,
		help='The directory where the docs will be generated. Default: /data/docs (i.e. /data/docs). Note: This is different from /data/services/docs which contains the sources and this script.'
	)

	(options, args) = parser.parse_args()

	return {
		'outputDirectory': options.outputDirectory
	}	


def write(filename, data):
	'''Write data to a file.
	'''
	fd = open(filename, 'w')
	fd.write(data)
	fd.close()


def main():
	options = getOptions()

	# Copy docs.css into the destination folder
	outputFilename = os.path.join(options['outputDirectory'], docsFilename)
	logger.info('Copying: ' + docsFilename + ' to ' + outputFilename)
	shutil.copy(docsFilename, outputFilename)

	# Generate all the docs
	mdwn = markdown.Markdown(safe_mode = 'escape', extensions = ['headerid'])

	indexList = ''
	inputFilenameRE = re.compile('^(.*)\.mdwn$')
	titleRE = re.compile('^# (.*)$', re.MULTILINE)
	sectionsRE = re.compile('^<h2 id="(.*)">(.*)</h2>$', re.MULTILINE)

	for inputFilename in os.listdir('.'):
		match = inputFilenameRE.match(inputFilename)
		if not match:
			continue

		outputName = match.groups()[0]
		outputFilename = os.path.join(options['outputDirectory'], outputName + '.html')

		logger.info('Generating: ' + outputFilename + ' from ' + inputFilename)

		fd = open(inputFilename, 'r')
		inputText = fd.read()
		fd.close()

		# If there is a line starting with # (i.e. <h1>), use it as the title.
		# Otherwise default to the outputName.
		title = outputName
		match = titleRE.search(inputText)
		if match:
			title = match.groups()[0]

		bodyText = mdwn.convert(inputText)

		# Search for sections (i.e. ##, <h2>) and build the index with them.
		# This is done after convert() because the headerid extension generates IDs for us automatically.
		index = None
		match = sectionsRE.search(bodyText)
		if match:
			index = '<h2>Index</h2><ol>'
			for section in sectionsRE.findall(bodyText):
				index += '<li><a href="#%s">%s</a></li>' % section
			index += '</ol>'

			# Put the index just before the first section
			# (so that the "abstract" or "introduction" is kept
			# after the title but before the index)
			firstSection = bodyText.find('<h2')
			bodyText = bodyText[:firstSection] + index + bodyText[firstSection:]

		outputText = docsTemplate % (title, docsFilename, bodyText)

		write(outputFilename, outputText)

		# Add the doc to the global index
		indexList += '<li><a href="%s">%s</a></li>' % (outputName + '.html', title)

	# Generate a simple docs' index (i.e. a list of the files)
	outputFilename = os.path.join(options['outputDirectory'], indexFilename)
	logger.info('Generating: ' + outputFilename)
	bodyText = '''
		<h1>%s</h1>
		<p>These are the documents available:
		<ul>
	''' % indexTitle
	bodyText += indexList
	bodyText += '</ul>'
	outputText = docsTemplate % (indexTitle, docsFilename, bodyText)
	write(outputFilename, outputText)


if __name__ == '__main__':
	main()

