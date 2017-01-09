import sys, os
binpath = os.path.dirname(__file__)
libpath = os.path.join(binpath,"../")
sys.path.append(libpath)
from cmn_classes import openNewSession
# Monday == 0
openNewSession()
print "# System update succesfully"

