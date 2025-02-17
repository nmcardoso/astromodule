import getpass
import os
import shelve
import subprocess
import tarfile
from argparse import ArgumentParser
from pathlib import Path
from time import sleep

from astropy.utils.data import download_file


def cbpf_up(args):
  user = os.environ.get('CBPF_USER')
  password = os.environ.get('CBPF_PASS')
  local = args.local[0]
  remote = args.remote[0]
  cmd = f"sshpass -p {password} rsync --mkpath -r -v --progress -e 'ssh -XY -p 13900' '{local}' {user}@tiomno.cbpf.br:'{remote}'"
  subprocess.call(cmd, shell=True)
  

def cbpf_down(args):
  user = os.environ.get('CBPF_USER')
  password = os.environ.get('CBPF_PASS')
  local = args.local[0]
  remote = args.remote[0]
  cmd = f"sshpass -p {password} rsync --mkpath -r -v --progress -e 'ssh -XY -p 13900' {user}@tiomno.cbpf.br:'{remote}' '{local}'"
  it = 0
  while it < args.repeat:
    print(f'Execution {it} of {args.repeat}')
    subprocess.call(cmd, shell=True)
    sleep(args.delay)
    it += 1
  

def cbpf_ssh(args):
  user = os.environ.get('CBPF_USER')
  password = os.environ.get('CBPF_PASS') 
  cmd = f"sshpass -p {password} ssh -XY -p 13900 {user}@tiomno.cbpf.br"
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
    
    
    

  
def db_install(args):
  url = 'https://downloads.mariadb.org/rest-api/mariadb/11.8.1/mariadb-11.8.1-linux-systemd-x86_64.tar.gz'
  
  install_path = Path(args.path)
  if install_path.exists() and install_path.is_dir():
    install_path = install_path / 'mariadb'
  
  tar_path = download_file(remote_url=url, show_progress=True, pkgname='astromodule', cache=True)
  with tarfile.open(tar_path) as tar:
    tar.extractall(install_path)
    
  user = getpass.getuser()
  base_dir = str((install_path / 'mariadb-11.8.1-linux-systemd-x86_64').resolve().absolute())
  data_dir = install_path / 'data'
  data_dir.mkdir(parents=True, exist_ok=True)
  data_dir = str(data_dir.resolve().absolute())
  pidfile_path = str((install_path / 'mariadbd.pid').resolve().absolute())
  socket_path = str((install_path / 'mariadbd.sock').resolve().absolute())
  client_socket_path = str((install_path / 'socket').resolve().absolute())
  conf_path = install_path / 'my.conf'
  install_script_path = str((install_path / 'mariadb-11.8.1-linux-systemd-x86_64' / 'scripts' / 'mariadb-install-db').resolve().absolute())
  
  conf_file = f"""
[server]
user={user}
basedir={base_dir}
datadir={data_dir}

[mariadbd]
pid-file={pidfile_path}
socket={socket_path}
port=31666

[client]
socket={client_socket_path}
  """.strip()
  conf_path.write_text(conf_file)
  
  subprocess.call(f'{install_script_path} --defaults-file={str(conf_path.absolute())} --auth-root-authentication-method=normal', shell=True)
  
  config_path = Path.home() / '.config' / 'astromodule' / 'db.conf'
  config_path.parent.mkdir(parents=True, exist_ok=True)
  with shelve.open(config_path) as conf:
    conf['MARIADB_PATH'] = base_dir
  

def db_start(args):
  config_path = Path.home() / '.config' / 'astromodule' / 'db.conf'
  with shelve.open(config_path) as conf:
    install_path = Path(conf['MARIADB_PATH'])
  mariadb_bin_path = str(install_path / 'bin' / 'mariadbd-safe')
  conf_path = str(install_path.parent / 'my.conf')
  subprocess.call(f'{mariadb_bin_path} --defaults-file={conf_path} &', shell=True)
  

def db_stop(args):
  subprocess.call(f'pkill -9 mariadb-safe', shell=True)


def db_client(args):
  config_path = Path.home() / '.config' / 'astromodule' / 'db.conf'
  with shelve.open(config_path) as conf:
    install_path = Path(conf['MARIADB_PATH'])
  mariadb_bin_path = str(install_path / 'bin' / 'mariadb')
  conf_path = str(install_path.parent / 'my.conf')
  subprocess.call(f'{mariadb_bin_path} --defaults-file={conf_path} -uroot --port 31666', shell=True)
  
  
def db_dump(args):
  config_path = Path.home() / '.config' / 'astromodule' / 'db.conf'
  with shelve.open(config_path) as conf:
    install_path = Path(conf['MARIADB_PATH'])
  mariadb_bin_path = str(install_path / 'bin' / 'mariadb-dump')
  conf_path = str(install_path.parent / 'my.conf')
  out_dir = Path(args.out)
  out_dir.mkdir(parents=True, exist_ok=True)
  subprocess.call(f'{mariadb_bin_path} --defaults-file={conf_path} -uroot --port 31666 --all-databases --dir={args.out}', shell=True)
  
  
def db_import(args):
  config_path = Path.home() / '.config' / 'astromodule' / 'db.conf'
  with shelve.open(config_path) as conf:
    install_path = Path(conf['MARIADB_PATH'])
  mariadb_bin_path = str(install_path / 'bin' / 'mariadb-import')
  conf_path = str(install_path.parent / 'my.conf')
  subprocess.call(f'{mariadb_bin_path} --defaults-file={conf_path} -uroot --port 31666 --dir={args.dir}', shell=True)


def db_port():
  print('31666')

def db():
  parser = ArgumentParser(
    prog='db', 
    description='Mariadb headless database'
  )
  
  subparser = parser.add_subparsers(dest='subprog')
  
  install = subparser.add_parser('install')
  install.add_argument('path')
  
  start = subparser.add_parser('start')
  
  stop = subparser.add_parser('stop')
  
  port = subparser.add_parser('port')
  
  client = subparser.add_parser('client')
  
  dump = subparser.add_parser('dump')
  dump.add_argument('out')
  
  imp = subparser.add_parser('import')
  imp.add_argument('dir')
  
  args = parser.parse_args()
  
  cmds = {
    'install': db_install,
    'start': db_start,
    'stop': db_stop,
    'port': db_port,
    'client': db_client,
    'dump': db_dump,
    'import': db_import,
  }
  
  handler = cmds.get(args.subprog)
  if handler:
    handler(args)
  else:
    parser.print_help()
  
  
if __name__ == "__main__":
  db()