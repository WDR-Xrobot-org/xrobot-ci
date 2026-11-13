#!/usr/bin/env python3
"""仅为WDR-Xrobot-org的HTTPS Git读取提供凭据；令牌由CI Secret注入。"""
import os
import sys


def credentials(request, token):
    fields = dict(line.split('=', 1) for line in request.splitlines() if '=' in line)
    if (fields.get('protocol') != 'https' or fields.get('host') != 'github.com'
            or not fields.get('path', '').casefold().startswith('wdr-xrobot-org/') or not token):
        return ''
    return 'username=x-access-token\npassword=' + token + '\n\n'


if __name__ == '__main__' and len(sys.argv) == 2 and sys.argv[1] == 'get':
    sys.stdout.write(credentials(sys.stdin.read(), os.environ.get('WDR_MODULES_READ_TOKEN', '')))
