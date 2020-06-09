# -*- coding: utf-8 -*-
# ansible API (结果回调类)
# 运行环境： python 3.6.8 + ansible 2.8.3

from ansible.plugins.callback import CallbackBase

class ResultCallback(CallbackBase):

    def __init__(self, *args, **kwargs):

        self.result = {}
        self.result['ok'] = {}
        self.result['unreachable'] = {}
        self.result['failed'] = {}


    def v2_runner_on_ok(self, result, **kwargs):

        self.result['ok'][result._host.get_name()] = result._result


    def v2_runner_on_unreachable(self, result):

        self.result['unreachable'][result._host.get_name()] = result._result


    def v2_runner_on_failed(self, result, *args, **kwargs):

        self.result['failed'][result._host.get_name()] = result._result

