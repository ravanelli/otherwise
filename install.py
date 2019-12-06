import os, sys, subprocess
from subprocess import check_call, check_output, CalledProcessError

python3 = [
    'apt install -y wget make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncurses5-dev libncursesw5-dev xz-utils tk-dev',
    'wget https://www.python.org/ftp/python/3.6.9/Python-3.6.9.tgz'
    ]

packages = [
    'apt update -y',
    'apt install -y git libsasl2-dev libldap2-dev libssl-dev \
    gcc make autoconf automake git python3-pip python3-requests \
    python3-mock gettext pkgconf xsltproc python3-dev pep8 pyflakes \
    python3-yaml systemd logrotate python3-psutil python3-lxml \
    python3-websockify openssl nginx python3-cherrypy3 python3-cheetah \
    python-m2crypto gettext python3-openssl bc libnl-route-3-dev \
    python3-configobj python3-lxml python3-magic python3-paramiko python3-ldap \
    spice-html5 novnc qemu-kvm python3-libvirt python3-parted python3-guestfs  \
    python3-pil python3-cherrypy3 libvirt0 libvirt-daemon-system \
    libvirt-clients nfs-common sosreport open-iscsi libguestfs-tools \
    libnl-route-3-dev python3-pampy libparted2 libparted-dev'
    ]

wok = [
    'git clone https://github.com/kimchi-project/wok.git /tmp/wok',
    'pip3 install -r /tmp/wok/requirements-UBUNTU.txt \
    python-ldap python-pam cherrypy Cheetah3 lxml psutil websockify jsonschema \
    pyOpenSSL requests libvirt-python distro pyparted ethtool'
    ]

kimchi = [
    'git clone https://github.com/kimchi-project/kimchi.git /tmp/wok/src/wok/plugins/kimchi/',
    'pip3 install -r /tmp/wok/src/wok/plugins/kimchi/requirements-dev.txt'
    ]

build = [['./autogen.sh', '--system'], ['make','install']]

python_build = [['./configure',' --enable-optimizations'], 
    ['make', '-j8'],['make', 'install']]

update_python = ['update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1',
    'update-alternatives --install /usr/bin/python python /usr/local/bin/python3.6 2']

def run_cmd(command):

    '''
    Run the given command using check_call and verify its return code.
    @param str command command to be executed
    '''

    try:
        check_call(command.split())
    except CalledProcessError as e:
        print('An exception has occurred: {0}'.format(e))
        sys.exit(1)

def execute_cmd(list, step):

    '''
    Execute the given commands using run_cmd function
    @param list list commands to be executed
    @param step str name of the comand to be executed
    '''

    print('Step: %s' % (step))

    for item in list:
        run_cmd(item)

def run_build(list, dir):
    '''
    Execute the given commands in other directory
    @param list list commands to be executed
    @param dir str directory path
    '''
    print(list,dir)
    try:
        build = subprocess.Popen(list, cwd=dir)
        build.wait()
    except CalledProcessError as e:
        print('An exception has occurred: {0}'.format(e))
        sys.exit(1)

def main():

    execute_cmd(python3, 'Intalling Python3')
    for py in python_build:
        run_build(py, '/home/ravanelli/Python-3.6.9')

    execute_cmd(update_python, 'Updating Python')
    execute_cmd(packages, 'Intalling necessary Packages')
    execute_cmd(wok, 'Installing wok')

    for item in build:
        run_build(item, '/tmp/wok/')

    execute_cmd(kimchi, 'Installing kimchi')
    for item in build:
        run_build(item, '/tmp/wok/src/wok/plugins/kimchi')
    print("All Good, Welcome to Kimchi")

    execute_cmd('python3 /tmp/wok/src/wokd', 'Running')

if __name__ == "__main__":
    main()
