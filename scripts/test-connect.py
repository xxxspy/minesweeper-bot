#!/usr/bin/python3
# 文件名：client.py

# 导入 socket、sys 模块
import socket
import sys
import time
import numpy as np

# 创建 socket 对象
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

# 获取本地主机名
host = '127.0.0.1'

# 设置端口号
port = 5678

# 连接服务，指定主机和端口
s.connect((host, port))

BUFFER_SIZE = 1024

for i in range(100):
    print('msg:', i)
    msg = s.recv(BUFFER_SIZE)
    print(msg)
    if msg == b'> ':
        break

for i in range(10):
    print('action:', i)
    s.send('click:{},{}'.format(i, i).encode('utf8'))
    time.sleep(1)
    s.send(b'get-map')
    while True:
        msg:bytes = s.recv(BUFFER_SIZE)
        print(msg)
        if b':' in msg:
            dtype, data = msg.split(b':')
            print('msg:', np.frombuffer(msg, dtype=dtype.decode('utf8')))
            break
s.close()

print (msg.decode('utf-8'))