#!/usr/bin/python

import os
import sys

sys.path.insert(0, "src/")

from get_sub import GetSub

def main(args):
	if len(args) != 2:
		sys.exit("usage: 'video.mp4' 'language'")

	gs = GetSub(0, 30, 300)	
	gs.download(args[0], args[1])
		

if __name__ == '__main__':
	main(sys.argv[1:])
