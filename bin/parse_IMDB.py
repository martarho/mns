from unidecode import unidecode
import sys
import re
#irgx = re.compile(r"(\d+)(tt\d+)")

#toprint = ["IDimdbID", "Title", "Year", "Rating", "Runtime", "Genre", "Released", "Poster", "Plot"]
toprint =  ["imdbID", "Title", "Year"]

for line in sys.stdin:
    cline = unidecode(line.rstrip())
    if cline.startswith("ID"):
        header = cline.rstrip().split("\t")
    else:
         l = cline.rstrip().split("\t")
	 #result  = rgx.match(l[0])
         #imdbid  = result.group(2)
         #otherid = result.group(1)
         if l[0] in l[1]:
                  
            d = dict(zip(header, l))
         
            p = [ d[x] for x in toprint ] 
         
            print "\t".join(p)
        
        
        
        
