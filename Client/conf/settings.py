import os

# 远端接收数据的服务器
Params = {
    'server': '192.168.0.100',
    'port': 8000,
    'url': '/assets/report/',
    'request_timeout': 30,
}

# 日志文件配置
PATh = os.path.join(os.path.dirname(os.getcwd(), 'log', 'cmdb.log'))
