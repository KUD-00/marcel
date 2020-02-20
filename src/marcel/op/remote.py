import io
import pickle
import subprocess
import sys

import marcel.core


class Remote(marcel.core.Op):
    def __init__(self, pipeline):
        super().__init__()
        self.host = None
        self.pipeline = pipeline
        self.process = None

    def __repr__(self):
        return 'remote(host=%s)' % self.host

    # BaseOp

    def setup_1(self):
        pass

    def receive(self, x):
        assert x is None, x
        # Start the remote process
        command = ' '.join([
            'ssh',
            '-l',
            self.host.user,
            self.host.ip_addr,
            'farcel.py'
        ])
        self.process = subprocess.Popen(command,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True,
                                        universal_newlines=False)
        # Pickle the pipeline so that it can be sent to the remote process
        buffer = io.BytesIO()
        pickler = pickle.Pickler(buffer)
        pickler.dump(self.pipeline)
        buffer.seek(0)
        stdout, stderr = self.process.communicate(input=buffer.getvalue())
        # Wait for completion (already guaranteed by communicate returning?)
        self.process.wait()
        # Handle results
        stderr_lines = stderr.decode('utf-8').split('\n')
        if len(stderr_lines[-1]) == 0:
            del stderr_lines[-1]
        for line in stderr_lines:
            print(line, file=sys.stderr)
        input = pickle.Unpickler(io.BytesIO(stdout))
        try:
            while True:
                x = input.load()
                self.send(x)
        except EOFError:
            self.send_complete()

    # Remote

    def set_host(self, host):
        self.host = host