# This file is part of Marcel.
# 
# Marcel is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or at your
# option) any later version.
# 
# Marcel is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Marcel.  If not, see <https://www.gnu.org/licenses/>.

import marcel.core
import marcel.exception
import marcel.util


class RunPipeline(marcel.core.Op):

    def __init__(self):
        super().__init__()
        self.var = None
        self.args_arg = None
        self.args = None
        self.kwargs_arg = None
        self.kwargs = None
        self.pipeline = None

    def __repr__(self):
        return f'runpipeline({self.var} {self.args_arg})'

    # AbstractOp

    def setup(self, env):
        self.args = self.eval_function(env, 'args_arg')
        self.kwargs = self.eval_function(env, 'kwargs_arg')
        self.pipeline = env.getvar(self.var)
        if self.pipeline is None:
            raise marcel.exception.KillCommandException(
                f'{self.var} is not executable.')
        if not isinstance(self.pipeline, marcel.core.Pipeline):
            raise marcel.exception.KillCommandException(
                f'The variable {self.var} is not bound to anything executable.')
        n_params = 0 if self.pipeline.parameters() is None else len(self.pipeline.parameters())
        if n_params != ((0 if self.args is None else len(self.args)) +
                        (0 if self.kwargs is None else len(self.kwargs))):
            raise marcel.exception.KillCommandException(
                f'Wrong number of arguments for pipeline {self.var} = {self.pipeline}')
        # Why copy: A pipeline can be used twice in a command, e.g.
        #    x = (| a: ... |)
        #    x (1) | join (| x (2) |)
        # Without copying the identical ops comprising x would be used twice in the same
        # command. This potentially breaks the use of Op state during execution, and also
        # breaks the structure of the pipeline, e.g. Op.receiver.
        self.pipeline = self.pipeline.copy()
        self.pipeline.set_error_handler(self.owner.error_handler)
        self.pipeline.last_op().receiver = self.receiver
        env.vars().push_scope(self.pipeline_args())
        try:
            self.pipeline.setup(env)
        finally:
            env.vars().pop_scope()

    # Op

    def run(self, env):
        env.vars().push_scope(self.pipeline_args())
        try:
            self.pipeline.run(env)
        finally:
            env.vars().pop_scope()

    def receive(self, env, x):
        env.vars().push_scope(self.pipeline_args())
        try:
            self.pipeline.receive(env, x)
        finally:
            env.vars().pop_scope()

    def flush(self, env):
        self.pipeline.flush(env)
        self.propagate_flush(env)

    def cleanup(self):
        self.pipeline.cleanup()

    # RunPipeline

    def set_pipeline_args(self, args, kwargs):
        self.args_arg = args
        self.kwargs_arg = kwargs

    def pipeline_args(self):
        map = None
        params = self.pipeline.parameters()
        if params is not None:
            map = {}
            # Set anonymous args
            if self.args is not None:
                if len(self.args) > len(params):
                    raise marcel.exception.KillCommandException(
                        f'Provided {len(self.args)} arguments, but there are only {len(params)} pipeline parameters')
                for i in range(len(self.args)):
                    map[params[i]] = self.args[i]
            # Set named args
            if self.kwargs is not None:
                already_set = set(map.keys()).intersection(self.kwargs.keys())
                if len(already_set) > 0:
                    raise marcel.exception.KillCommandException(
                        f'Attempt to set these arguments twice (anonymous and named): {already_set}')
                map.update(self.kwargs)
            if len(map) != len(params):
                raise marcel.exception.KillCommandException(f'Expected arguments: {len(params)}, given: {len(map)}')
        return map
