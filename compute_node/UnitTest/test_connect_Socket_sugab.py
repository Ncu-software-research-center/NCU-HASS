import socket

HOST = "10.0.0.24"
PORT = 5001

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST,PORT))
s.send("update instance")

s.send("get instance")

