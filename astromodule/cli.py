import os
import subprocess
from argparse import ArgumentParser
from time import sleep


def cbpf_up(args):
  user = os.environ.get('CBPF_USER')
  password = os.environ.get('CBPF_PASS')
  local = args.local[0]
  remote = args.remote[0]
  cmd = f"sshpass -p {password} rsync --mkpath -r -v --progress -e 'ssh -p 13900' '{local}' {user}@tiomno.cbpf.br:'{remote}'"
  subprocess.call(cmd, shell=True)
  

def cbpf_down(args):
  user = os.environ.get('CBPF_USER')
  password = os.environ.get('CBPF_PASS')
  local = args.local[0]
  remote = args.remote[0]
  cmd = f"sshpass -p {password} rsync --mkpath -r -v --progress -e 'ssh -p 13900' {user}@tiomno.cbpf.br:'{remote}' '{local}'"
  it = 0
  while it < args.repeat:
    print(f'Execution {it} of {args.repeat}')
    subprocess.call(cmd, shell=True)
    sleep(args.delay)
    it += 1
  

def cbpf_ssh(args):
  user = os.environ.get('CBPF_USER')
  password = os.environ.get('CBPF_PASS') 
  cmd = f"sshpass -p {password} ssh -p 13900 {user}@tiomno.cbpf.br"
  subprocess.call(cmd, shell=True)


def cbpf():
  parser = ArgumentParser(
    prog='cbpf', 
    description='CBPF cluster access'
  )
  
  subparser = parser.add_subparsers(dest='subprog')
  
  down = subparser.add_parser('down')
  down.add_argument('-r', '--repeat', type=int, default=1, action='store', help='number of times to repeat')
  down.add_argument('-d', '--delay', type=int, default=120, action='store', help='delay time in seconds')
  down.add_argument('remote', nargs=1)
  down.add_argument('local', nargs='+')
  
  up = subparser.add_parser('up')
  up.add_argument('local', nargs=1) 
  up.add_argument('remote', nargs='+')
  
  subparser.add_parser('ssh')
  
  args = parser.parse_args()
  
  cmds = {
    'down': cbpf_down,
    'up': cbpf_up,
    'ssh': cbpf_ssh
  }
  
  handler = cmds.get(args.subprog)
  if handler:
    handler(args)
  else:
    parser.print_help()
  
  
  
  


def teiu_up(args):
  user = os.environ.get('TEIU_USER')
  password = os.environ.get('TEIU_PASS')
  local = args.local[0]
  remote = args.remote[0]
  url = 'teiu.iag.usp.br' if not args.ip else '10.180.0.110'
  cmd = f"sshpass -p {password} rsync --mkpath -r -v --progress -e ssh '{local}' {user}@{url}:'{remote}'"
  subprocess.call(cmd, shell=True)


def teiu_down(args):
  user = os.environ.get('TEIU_USER')
  password = os.environ.get('TEIU_PASS')
  local = args.local[0]
  remote = args.remote[0]
  url = 'teiu.iag.usp.br' if not args.ip else '10.180.0.110'
  cmd = f"sshpass -p {password} rsync --mkpath -r -v --progress -e ssh {user}@{url}:'{remote}' '{local}'"
  subprocess.call(cmd, shell=True)
  
  
def teiu_ssh(args):
  user = os.environ.get('TEIU_USER')
  password = os.environ.get('TEIU_PASS') 
  url = 'teiu.iag.usp.br' if not args.ip else '10.180.0.110'
  cmd = f"sshpass -p {password} ssh {user}@{url}"
  subprocess.call(cmd, shell=True)


def teiu():
  parser = ArgumentParser(
    prog='cbpf', 
    description='Teiu cluster access'
  )
  
  subparser = parser.add_subparsers(dest='subprog')
  
  down = subparser.add_parser('down')
  down.add_argument('remote', nargs=1)
  down.add_argument('local', nargs='+')
  down.add_argument('--ip', action='store_true')
  
  up = subparser.add_parser('up')
  up.add_argument('local', nargs=1) 
  up.add_argument('remote', nargs='+')
  up.add_argument('--ip', action='store_true')
  
  ssh = subparser.add_parser('ssh')
  ssh.add_argument('--ip', action='store_true')
  
  args = parser.parse_args()
  
  cmds = {
    'down': teiu_down,
    'up': teiu_up,
    'ssh': teiu_ssh
  }
  
  handler = cmds.get(args.subprog)
  if handler:
    handler(args)
  else:
    parser.print_help()




def iguana_up(args):
  user = os.environ.get('IGUANA_USER')
  password = os.environ.get('IGUANA_PASS')
  local = args.local[0]
  remote = args.remote[0]
  url = 'iguana.iag.usp.br' if not args.ip else '10.180.0.180'
  cmd = f"sshpass -p {password} rsync --mkpath -r -v --progress -e ssh '{local}' {user}@{url}:'{remote}'"
  subprocess.call(cmd, shell=True)


def iguana_down(args):
  user = os.environ.get('IGUANA_USER')
  password = os.environ.get('IGUANA_PASS')
  local = args.local[0]
  remote = args.remote[0]
  url = 'iguana.iag.usp.br' if not args.ip else '10.180.0.180'
  cmd = f"sshpass -p {password} rsync --mkpath -r -v --progress -e ssh {user}@{url}:'{remote}' '{local}'"
  subprocess.call(cmd, shell=True)
  
  
def iguana_ssh(args):
  user = os.environ.get('IGUANA_USER')
  password = os.environ.get('IGUANA_PASS') 
  url = 'iguana.iag.usp.br' if not args.ip else '10.180.0.180'
  cmd = f"sshpass -p {password} ssh {user}@{url}"
  subprocess.call(cmd, shell=True)



def iguana():
  parser = ArgumentParser(
    prog='cbpf', 
    description='Iguana cluster access'
  )
  
  subparser = parser.add_subparsers(dest='subprog')
  
  down = subparser.add_parser('down')
  down.add_argument('remote', nargs=1)
  down.add_argument('local', nargs='+')
  down.add_argument('--ip', action='store_true')
  
  up = subparser.add_parser('up')
  up.add_argument('local', nargs=1) 
  up.add_argument('remote', nargs='+')
  up.add_argument('--ip', action='store_true')
  
  ssh = subparser.add_parser('ssh')
  ssh.add_argument('--ip', action='store_true')
  
  args = parser.parse_args()
  
  cmds = {
    'down': iguana_down,
    'up': iguana_up,
    'ssh': iguana_ssh
  }
  
  handler = cmds.get(args.subprog)
  if handler:
    handler(args)
  else:
    parser.print_help()
  
  
if __name__ == "__main__":
  cbpf()