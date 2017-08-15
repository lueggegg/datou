warning = "generated by script, do not edit it yourself\n\n\n"

filename = 'type_define.txt'
py_target = 'type_define.py'
js_target = './template/res/script/type_define.js'

src = open(filename, 'r')
py_des = open(py_target, 'w')
js_des = open(js_target, 'w')

py_des.write('# %s' % warning)
js_des.write('// %s' % warning)
for line in src:
    py_des.write(line)
    if line.rstrip():
        js_des.write('var %s;\n' % line[:-1])
    else:
        js_des.write(line)

src.close()
py_des.close()
js_des.close()