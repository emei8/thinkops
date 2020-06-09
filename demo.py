# -*- coding: utf-8 -*-
# ansible API (测试文件)
# 运行环境： python 3.6.8 + ansible 2.8.3

import json
from ansible_api.ansible_runner import AnsibleRunner

runner = AnsibleRunner(
            sources='hosts',
            pattern="all",
            remote_user="root",
        )

#运行ansible命令行
#res = runner.ansible('shell','ls')


#运行playbook文件
res = runner.playbook(['site.yml'])

print(json.dumps(res, indent=4))

