import socket
import sys
import time
import statistics

ver_num = 2  # 定义消息的版本号

def main():
    if len(sys.argv) != 3:  # 检查命令行参数数量是否正确
        print("Usage: python UDPClient.py serverIP serverPort")  # 打印使用方法
        return
    Server_ip = sys.argv[1]  # 获取命令行参数中的服务器IP地址
    Server_port = int(sys.argv[2])  # 获取命令行参数中的服务器端口号，并转换为整数
    timeout = 0.1  # 设置超时时间为100毫秒
    max_sendtimes = 3  # 设置最大发送次数为3次

    # 创建一个UDP套接字
    Client_Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 设置套接字超时时间为100毫秒
    Client_Socket.settimeout(timeout)

    sequence_no = 1  # 初始化序列号为1
    sent_packets = 0  # 初始化发送的数据包数量为0
    received_packets = 0  # 初始化接收的数据包数量为0
    RTT_list = []  # 初始化RTT列表
    first_response_time = None  # 初始化第一次响应时间
    last_response_time = None  # 初始化最后一次响应时间

    # 构造发送的packet
    def send_packet(seq_no, info_type):
        message = seq_no.to_bytes(2, 'big') + bytes([ver_num]) + bytes([info_type]) * 200
        Client_Socket.sendto(message, (Server_ip, Server_port))

    try:
        send_packet(0, 1)  # 发送握手包，序列为0，标识为1
        response_message, _ = Client_Socket.recvfrom(1024)  # 接收服务端发送的数据，最大接收 1024 字节
        if response_message[3] == 1:   # 客户端与服务器端的连接建立
            send_packet(0, 5)  # 发送握手包，序列为0，标识为5
            # 发送12个待发送的数据包
            while sequence_no <= 12:
                # 每个包初始重传次数为0
                send_times = 0
                while send_times < max_sendtimes:
                    send_packet(sequence_no, 2)  # 发送数据包，序列号即为第几个报文号，标识为2
                    start_time = time.time()  # 记录开始时间
                    sent_packets += 1  # 发送数据包数量加1
                    send_times += 1  # 重传次数加1

                    try:
                        response_message, _ = Client_Socket.recvfrom(1024)  # 接收服务器响应
                        end_time = time.time()  # 记录结束时间
                        RTT = (end_time - start_time) * 1000  # 计算RTT（毫秒）
                        # 解析接收到的序列号
                        recv_seq_no = int.from_bytes(response_message[0:2], 'big')
                        # 如果序列号匹配
                        if recv_seq_no == sequence_no:
                            received_packets += 1  # 接收数据包数量加1
                            RTT_list.append(RTT)  # 添加RTT到列表
                            if first_response_time is None:
                                first_response_time = time.time()  # 记录第一次响应时间
                            last_response_time = time.time()  # 更新最后一次响应时间
                            print(f"Seq: {sequence_no},{Server_ip}:{Server_port} 、RTT: {RTT:.2f} ms")
                            break
                    except socket.timeout:  # 如果超时
                        # 如果重传次数小于最大重传次数
                        if send_times < max_sendtimes:
                            print(f"Seq: {sequence_no}, request time out, retrying...")
                        else:
                            print(f"Seq: {sequence_no}, all attempts failed, packet lost")

                sequence_no += 1  # 序列号加1

            send_packet(sequence_no, 3)  # 四次挥手第一次，序列号为13，标识为3
            message1, _ = Client_Socket.recvfrom(1024)  # 接受服务器的确认包
            if message1[3] == 3:
                message2, _ = Client_Socket.recvfrom(1024)  # 收到服务器的请求
                if message2[3] == 4:
                    send_packet(sequence_no, 4)  # 发送确认结束包，序列为13，标识为4
                    Client_Socket.close()  # 关闭套接字
    except socket.error:  # 如果发生套接字错误
        print(f"建立连接失败，请重新建立连接！")
    finally:
        Client_Socket.close()  # 关闭套接字

    # 如果有成功接收的数据包，则进行汇总
    if received_packets > 0:
        loss_rate = ((sent_packets - received_packets) / sent_packets) * 100  # 计算丢包率
        max_rtt = max(RTT_list)  # 计算最大RTT
        min_rtt = min(RTT_list)  # 计算最小RTT
        avg_rtt = sum(RTT_list) / len(RTT_list)  # 计算平均RTT
        stddev_rtt = statistics.stdev(RTT_list)  # 计算RTT的标准差

        # 打印汇总信息
        print("\n汇总:")
        print(f"Successful packets: {received_packets}")  # 打印成功接收的数据包数量
        print(f"Packet loss rate: {loss_rate:.2f}%")
        print(f"Max RTT: {max_rtt:.2f} ms")
        print(f"Min RTT: {min_rtt:.2f} ms")
        print(f"Avg RTT: {avg_rtt:.2f} ms")
        print(f"RTT StdDev: {stddev_rtt:.2f}")
        # 计算总响应时间
        if first_response_time and last_response_time:
            total_response_time = (last_response_time - first_response_time) * 1000
            print(f"Total server response time: {total_response_time:.2f} ms")


if __name__ == "__main__":
    main()
