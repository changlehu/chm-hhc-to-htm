# windows系统自动反编译chm，并拷贝convert_hhc.py到目录下的脚本
import re,codecs
import requests,json
import os,sys,glob
files=glob.glob("*.chm")
for filename in files:
	name=os.path.splitext(os.path.basename(filename))[0]
	os.system(f"hh -decompile {name} {filename}")
	os.system(f"copy convert_hhc.py {name}")
print ("done!")

