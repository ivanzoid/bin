#!/usr/bin/env python

from xml.dom.minidom import parse
import sys

class NotTextNodeError:
	pass

def getTextFromNode(node):
	"""
	scans through all children of node and gathers the
	text. if node has non-text child-nodes, then
	NotTextNodeError is raised.
	"""
	t = ""
	for n in node.childNodes:
		if n.nodeType == n.TEXT_NODE:
			t += n.nodeValue
		else:
			raise NotTextNodeError
	return t

def nodeToDic(node):
	dic = {} 
	for n in node.childNodes:
		if n.nodeType != n.ELEMENT_NODE:
			continue
		if n.getAttribute("multiple") == "true":
			l = []
			for c in n.childNodes:
				if c.nodeType != n.ELEMENT_NODE:
					continue
				l.append(nodeToDic(c))
				dic.update({n.nodeName:l})
			continue

		try:
			text = getTextFromNode(n)
		except NotTextNodeError:
			dic.update({n.nodeName:nodeToDic(n)})
			continue

		# text node
		dic.update({n.nodeName:text})
		continue
	return dic

def readXml(filename):
	dom = parse(filename)
	return nodeToDic(dom)


def main():
	if len(sys.argv) < 2:
		print 'no file, no work'
		exit(0)

	dic = readXml(sys.argv[1])

	print repr(dic)

if __name__ == "__main__":
	main()

