import os
import time

domain = "sjtu.edu.cn"
f = open("fulldomain/resolved_domain/"+domain+".txt")
for d in f:
    out = os.popen("fierce --domain "+d+" --wide")
    print(out.read())
    time.sleep(100)
f.close()
