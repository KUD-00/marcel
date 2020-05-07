import marcel.core
import marcel.job


SUMMARY = '''
List the currently running jobs. This includes jobs that are currently paused.
'''


DETAILS = '''
The jobs listed may be running, denoted as {n:(+)}; or paused, denoted as {n:(-)}.
While it is extremely unlikely, a job that is no longer running may be displayed
also, denoted as {n:(x)}. 
    
Every job includes a job number and a process id. Note that job numbers may change over time,
as a job number simply reflects the job's position in the list of jobs. Process ids never change.
'''


def jobs():
    return Jobs()


class JobsArgParser(marcel.core.ArgParser):

    def __init__(self, env):
        super().__init__('jobs', env, SUMMARY, DETAILS)


class Jobs(marcel.core.Op):

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return f'jobs'

    # BaseOp
    
    def setup_1(self):
        pass

    def receive(self, x):
        job_id = 0
        for job in marcel.job.JobControl.only.jobs():
            # TODO: If job were a marcel.object, then it would have render_compact/full methods.
            description = f'{job_id}({job.state_symbol()}): {job.process.pid}  {job.command.source}'
            self.send(description)
            job_id += 1

