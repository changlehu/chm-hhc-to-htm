# chm-hhc-to-htm
convert hhc and hhk files to htm in decompiled chm directory. 

把反编译后的chm目录中的hhc和hhk转为htm，并生成新的index.htm

在window系统中，chm反编译的方法：

hh -decompile C:\Users\Administrator\Desktop\a a.chm

这样反编译的目录中，会有hhc和hhk文件，是chm的目录文件。再使用这个脚本程序把这两个文件转成htm，并自动生成index.htm

python convert_hhc.py

按要求输入目录 C:\Users\Administrator\Desktop\a

也可以是相对目录，如果python脚本直接放到chm反编译的目录中，目录可以输入 .

完成后打开 index.htm
