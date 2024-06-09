import socket
import struct
import threading

My_SERVER_IP = '192.168.72.130'
My_SERVER_PORT = 1117
# 报文类型
Initialization = 1
agree = 2
reverseRequest = 3
reverseAnswer = 4

# 反转数据的函数
def data_reverse(data):
    return data[::-1]

# 解析报文的函数
def analyz_message(message):
    if len(message) >= 2:
        type = struct.unpack('!H', message[:2])[0]
        if type == Initialization:
            if len(message)<6:
                print("报文数据段缺失！")
            else:
                _,length = struct.unpack('!HI', message[:6]) #请求反转的字符串数量
                return type, length
        elif type == reverseRequest:
            if len(message) < 6:
                print("报文数据段缺失！")
            else:
                _,length = struct.unpack('!HI', message[:6])
                return type, length
        else:
            raise ValueError("未知报文类型")
    else:
        print("未知报文！")
        return

# 处理客户端连接的函数
def handle_client(client_socket, client_addr):
    client_socket.settimeout(1)  # 设置超时时间为1秒
    try:
        # 接收 Initialization 报文
        message = client_socket.recv(1024)
        type, blocks = analyz_message(message)
        if type == Initialization:
            print(f"服务器接收到 Initialization 报文，块数: {blocks}")
            # 发送 agree 报文
            agree_response = struct.pack('!H', agree)
            client_socket.send(agree_response)
            print("服务器发送 agree 报文")
            # 接收并处理 reverseRequest 报文
            for _ in range(blocks):
                message = client_socket.recv(1024)  # 2字节类型 + 4字节长度
                type,length = analyz_message(message)
                if type == reverseRequest:
                    data = message[6:6 + length].decode("utf-8")
                    print(f"服务器接收到数据，长度: {length}")
                    # 反转数据并发送 reverseAnswer 报文
                    reversed_data = data_reverse(data)
                    response = struct.pack('!HI', reverseAnswer,length) + reversed_data.encode("utf-8")
                    client_socket.send(response)
                    print(f"服务器发送反转数据，长度: {length}")
            print(f"已与客户端{client_addr}断开连接，且请求处理完毕")
        else:
            print("服务器接收到未知类型的报文")
    except socket.timeout:
        print(f"客户端{client_addr}连接超时")
    except socket.error as e:
        print(f"客户端{client_addr}异常断开连接: {e}")
    finally:
        client_socket.close()

# 在指定端口监听客户端连接
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((My_SERVER_IP, My_SERVER_PORT))
server_socket.listen(15)  # 允许最多15个客户端连接
print(f"服务器监听在 {My_SERVER_IP}:{My_SERVER_PORT}")

# 接收客户端连接
try:
    while True:
        client_socket, client_addr = server_socket.accept()
        print(f"客户端{client_addr}已连接")
        # 在新线程中处理客户端连接
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_addr))
        client_thread.start()
except KeyboardInterrupt:
    print("服务器关闭")
finally:
    server_socket.close()
