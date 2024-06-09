import socket
import random
from datetime import datetime

# 服务器的IP地址和端口号
My_SERVER_IP = '192.168.72.130'
My_SERVER_PORT = 1117

# 定义丢包的概率
LOSS_RATE = 0.3  #

# 创建一个IPv4地址族和UDP协议的socket对象
SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# 将socket绑定到指定的IP地址和端口号
SERVER_SOCKET.bind((My_SERVER_IP, My_SERVER_PORT))
# 服务器已准备
print(f"Server is ready to receive on IP {My_SERVER_IP} and port {My_SERVER_PORT}")

# 无限循环，等待客户端发送数据
while True:
    try:
        # 接收客户端发送的数据，最大接收1024字节，message为接收到的数据，Client_address为发送数据的客户端的地址
        message, Client_address = SERVER_SOCKET.recvfrom(1024)
        # 从接收到的消息中提取序列号，使用大端排序（高字节在低地址，低字节在高地址）
        sequence_no = int.from_bytes(message[0:2], 'big')
        # 提取消息中的版本号
        ver_num = message[2]
        # 检查版本号是否为2
        if ver_num == 2:
            # 处理不同类型的消息
            if message[3] == 1:  # '1'表示握手包
                # 构造响应消息，包含序列号、版本号和当前时间
                Response_message = sequence_no.to_bytes(2, 'big') + bytes([ver_num]) + bytes([1]) + bytes(datetime.now().strftime("%H-%M-%S"),
                                                                                    'utf-8').ljust(199, b'\x00')
                # 将响应消息发送回客户端
                SERVER_SOCKET.sendto(Response_message, Client_address)
                message2, _ = SERVER_SOCKET.recvfrom(1024)
                if message[3] == 5:
                    print("连接建立！")
            elif message[3] == 3:  # '3' 表示第一次挥手结束包
                # 构造响应消息，包含序列号、版本号和当前时间
                Response_message = sequence_no.to_bytes(2, 'big') + bytes([ver_num]) + bytes([3]) + bytes(
                    datetime.now().strftime("%H-%M-%S"),
                    'utf-8').ljust(199, b'\x00')
                # 将响应消息发送回客户端
                SERVER_SOCKET.sendto(Response_message, Client_address)
                # 再次构造响应消息，用于四次挥手的第二次响应
                Response_message = sequence_no.to_bytes(2, 'big') + bytes([ver_num]) + bytes([4]) + bytes(
                    datetime.now().strftime("%H-%M-%S"),
                    'utf-8').ljust(199, b'\x00')
                # 再次将响应消息发送回客户端
                SERVER_SOCKET.sendto(Response_message, Client_address)
                message2, _ = SERVER_SOCKET.recvfrom(1024)  # 接收客户端的最终确认包
                if message2[3] == 4:  # '4' 表示第二次挥手结束包
                    print(f"连接释放")
            elif message[3] == 2:  # '2' 表示packet包
                if random.random() > LOSS_RATE:  # 如果随机数大于丢包概率，则处理消息
                    # 构造响应消息，包含序列号、版本号和当前时间
                    Response_message = sequence_no.to_bytes(2, 'big') + bytes([ver_num]) + bytes(
                        datetime.now().strftime("%H-%M-%S"),
                        'utf-8').ljust(200, b'\x00')
                    # 将响应消息发送回客户端
                    SERVER_SOCKET.sendto(Response_message, Client_address)
                    # 打印响应序列号的信息
                    print(f"Responded to Seq: {sequence_no}")
                else:
                    # 如果随机数小于或等于丢包概率，则丢弃包
                    print(f"Dropped packet with Seq: {sequence_no}")
            # elif message[3] == 4:  # '4' 表示第二次挥手结束包
            #     print(f"连接释放")
            else:
                # 如果收到未知类型报文则丢弃并提示
                print("报文解析错误！")
        else:
            # 如果版本号不正确，则打印错误信息
            print("版本号不正确")
    except KeyboardInterrupt:
        # 捕获键盘中断异常
        print("异常错误，请检查！")
        break
# 关闭服务器socket
SERVER_SOCKET.close()
