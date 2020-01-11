#!/usr/bin/env python

""" 把客户端信息收集脚本做成windows和linux两个不同的版本
通过 os 和 sys 模块的配合，将当前客户端所在目录设置为工作目录，如果不这么做，会无法导入其它模块；
handler 模块是核心代码模块，在 core 目录中，我们一会来实现它。
以后调用客户端就只需要执行python main.py 参数就可以了
"""

import os
import sys
from core import handler

BASE_DIR = os.path.dirname(os.getcwd())
# 设置工作目录, 使得包和模块能够正常导入
sys.path.append(BASE_DIR)


if __name__ == "__main__":
    handler.ArgvHandler(sys.argv)
