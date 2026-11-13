#!/usr/bin/env python3
"""为当前隔离CI容器配置私有模块读取；不将令牌写入配置文件。"""
import os
from pathlib import Path
import shlex
import subprocess
import sys

if not os.environ.get('WDR_MODULES_READ_TOKEN'):
    raise SystemExit('请为调用仓库配置WDR_MODULES_READ_TOKEN，只读访问WDR-Xrobot-org模块和xrobot-ci。')
helper = Path(__file__).with_name('credential_helper.py').resolve()
for key, value in [
    ('credential.useHttpPath', 'true'),
    ('credential.helper', shlex.quote(sys.executable) + ' ' + shlex.quote(str(helper))),
]:
    subprocess.run(['git', 'config', '--global', '--replace-all', key, value], check=True)
