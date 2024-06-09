import socket
import struct
import random
import sys

# 报文类型
Initialization = 1
agree = 2
reverseRequest = 3
reverseAnswer = 4
output_filename = "resorted.txt"
filename = "test.txt"

# 读取文件并按随机长度分割
def split_file(filename, Lmin, Lmax, block_lens=[]):
    with open(filename, 'rb') as file:  # 以二进制形式读取文件
        file_content = file.read()
        # 去除文件内容中的\r和\n字符
        file_content = file_content.replace(b'\r', b'').replace(b'\n', b'')
        file_len = len(file_content)

    # 如果文件长度无法满足要求，则给出提示并退出
    if file_len < Lmin:
        print(f"文件总长度为{file_len}，您输入的Lmin值太大，请重新输入！")
        sys.exit(1)

    # 随机生成不同的块长
    temp = file_len
    while temp > 0:
        length = random.randint(Lmin, Lmax)
        if temp >= length:
            block_lens.append(length)
            temp -= length
        else:
            block_lens.append(temp)
            temp = 0
# 客户端处理过程，包括生成文件、发送数据、接收反转数据并保存
def client_process(client_socket,blocks):
    num = 0
    client_socket.settimeout(0.1)  # 设置超时时间为0.1秒
    try :
        with open(output_filename, 'w') as write_file:
            with open(filename,'rb') as read_file:
                # 发送 Initialization 报文
                request = struct.pack('!HI', Initialization,len(blocks))
                client_socket.send(request)
                # 接收 agree 报文
                client_socket.settimeout(0.1)  # 设置超时时间为0.1秒
                try:
                    agree_response = client_socket.recv(1024)
                    type = struct.unpack('!H', agree_response[:2])[0]
                    if type == agree:
                        # 发送 reverseRequest 报文和接收 reverseAnswer 报文
                        for block in blocks:
                            data = read_file.read(block)
                            # 去除数据中的\r（回车）和\n（换行）字符
                            data = data.replace(b'\r', b'').replace(b'\n', b'')
                            actual_length = len(data)  # 获取实际读取的数据长度
                            request_message = struct.pack('!HI', reverseRequest,actual_length) + data
                            client_socket.send(request_message)
                            print(f"客户端发送第 {num + 1} 块原数据，长度: {actual_length}")
                            print(f"{data}")

                            # 接收 reverseAnswer 报文
                            answer_response = client_socket.recv(1024)
                            if len(answer_response) < 6:
                                print("数据包损坏！")
                                continue
                            else:
                                type, length = struct.unpack('!HI', answer_response[:6])
                                if type == reverseAnswer:
                                    num+=1
                                    reversed_data =  answer_response[6:6 + length].decode("utf-8")
                                    print(f"客户端收到第{num}块反转数据：{ reversed_data}")
                                    write_file.write(reversed_data + "\n")
                    else:
                        print("连接超时，未收到服务器的回应")
                        client_socket.close()
                        return
                except socket.timeout:
                    print("连接超时，未收到服务器的回应")
                    client_socket.close()
                    return
    except socket.timeout:
        print("连接超时，未收到服务器的回应")
        exit(1)
    except socket.error:
        print("服务器端异常关闭，请重新检查！")
        exit(1)


def main():
    if len(sys.argv) != 5:
        print("Usage: python TCPClient.py serverIP serverPort Lmin Lmax")  # 打印使用方法
        return
    # 测试客户端和服务器交互
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    L_MIN = int(sys.argv[3])
    L_MAX = int(sys.argv[4])
    if L_MIN>L_MAX:
        print("输入的L_MIN不能大于L_MAX，请重新输入！")
        return
    my_blocks = []
    split_file(filename,L_MIN,L_MAX,my_blocks)
    N = len(my_blocks)
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))
        print(f"客户端已连接到服务器 {server_ip}:{server_port}")
        print(f"客户端发送数据块数：{N}块")
        # 客户端处理过程
        client_process(client_socket,  my_blocks)
    except socket.error:
        print(f"服务器端({server_ip}:{server_port})未开启或异常关闭，请重新连接！")
        sys.exit(1)

if __name__ == '__main__':
    main()