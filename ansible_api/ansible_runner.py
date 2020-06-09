# -*- coding: utf-8 -*-
# ansible API (核心类)
# 运行环境： python 3.6.8 + ansible 2.8.3


import shutil
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible import context
import ansible.constants as C
from ansible.module_utils.common.collections import ImmutableDict
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible_api.result_callback import ResultCallback


class AnsibleRunner(object):

    def __init__(
        self,
        sources='hosts',
        pattern="all",
        remote_user="root",

    ):
        self.sources = sources
        self.pattern = pattern
        self.remote_user = remote_user

        self.passwords = dict(vault_pass='secret')

        # initialize needed objects
        self.loader = DataLoader() # Takes care of finding and reading yaml, json and ini files

        # create inventory, use path to host config file as source or hosts in a comma separated string
        self.inventory = InventoryManager(loader=self.loader, sources=self.sources)

        # variable manager takes care of merging all the different sources to give you a unified view of variables available in each context
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)

        # since the API is constructed for CLI it expects certain options to always be set in the context object
        context.CLIARGS = ImmutableDict(
            connection='smart',  # local, smart, persistent
           # module_path=['/to/mymodules'], 
            forks=10, 
            become=True,
            become_method='sudo', 
            become_user='root', 
            remote_user=self.remote_user, 
            check=False,
            passwords=None,
            private_key_file=None,
            inventory=self.inventory,
            listtags=False,
            listtasks=False,
            listhosts=False,
            syntax=False,
            verbosity=2,
            extra_vars=None,
            timeout=C.DEFAULT_TIMEOUT,
            ssh_common_args=None,
            ssh_extra_args=None,
            sftp_extra_args=None,
            scp_extra_args=None,
            start_at_task=None,
        )

        # Instantiate our ResultCallback for handling results as they come in. Ansible expects this to be one of its main display outlets
        self.results_callback = ResultCallback()


    def ansible(self,module='shell',args='ls'):
        # create data structure that represents our play, including tasks, this is basically what our YAML loader does internally.
        play_source =  dict(
                name = "Ansible Play",
                hosts = self.pattern,
                gather_facts = 'no',
                tasks = [
                    dict(action=dict(module=module, args=args), register='shell_out'),
                    dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
                ]
            )

        # Create play object, playbook objects use .load instead of init or new methods,
        # this will also automatically create the task objects from the info provided in play_source
        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        # Run it - instantiate task queue manager, which takes care of forking and setting up all objects to iterate over host list and tasks
        tqm = None
        try:
            tqm = TaskQueueManager(
                    inventory=self.inventory,
                    variable_manager=self.variable_manager,
                    loader=self.loader,
                    passwords=self.passwords,
                    stdout_callback=self.results_callback,  # Use our custom callback instead of the ``default`` callback plugin, which prints to stdout
                    run_additional_callbacks=C.DEFAULT_LOAD_CALLBACK_PLUGINS,
                )

            tqm.run(play) # most interesting data for a play is actually sent to the callback's methods
            
            return self.results_callback.result
        
        finally:
            # we always need to cleanup child procs and the structures we use to communicate with them
            if tqm is not None:
                tqm.cleanup()

            # Remove ansible tmpdir
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

    
    def playbook(self,playbook_path):
        try:
            playbook = PlaybookExecutor(playbooks=playbook_path,
                                        inventory=self.inventory,
                                        variable_manager=self.variable_manager,
                                        loader=self.loader, 
                                        passwords=self.passwords)

            if playbook._tqm:
                playbook._tqm._stdout_callback = self.results_callback

            playbook.run()

            return self.results_callback.result

        except Exception as e:
            raise Exception(e)
  