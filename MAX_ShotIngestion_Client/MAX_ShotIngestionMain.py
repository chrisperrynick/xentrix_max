import os
import subprocess


def main(shot_list, maya_exe, seq_path):
    """

    :return:
    """

    cmd = ('"{mayaexe}" -command "python(\\"import sys;import os;sys.path.append(os.getcwd());'
           'import MAX_ShotIngestion as MSI;'
           ' reload(MSI); result = MSI.main(\'{sName}\',\'{seq_path}\');\\")"')

    for shot in shot_list:
        print('>>>>>>>>>>>>>>>', shot)
        run_command(cmd, maya_exe, shot, seq_path)


def run_command(command, maya_exe, sName, seq_path):
    command = command.format(mayaexe=maya_exe, sName=sName, seq_path=seq_path)
    print("command >>>>> ", command)
    process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    process.wait()

    result, error = process.communicate()
    result = result.decode().strip()
    error = error.decode().strip()
    trace = ''
    if error:
        trace = error
    # elif process.returncode != 0:
    #     trace = "UnExpected error occurred while running the batch"
    else:
        trace = get_traceback(result)

    if trace:
        print("trace  >>>>> ", trace)
        raise ValueError(trace)


def get_traceback(data):
    flag = False
    error = []
    for e in data.split('\r\n'):
        if 'Traceback' in e:
            flag = True
        if flag:
            if 'Error:' in e:
                flag = False
                e = "#" * 50
                e += '\n'
            error.append(e.split('LogPython: Error: ')[-1])

    return '\n'.join(error)
