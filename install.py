import argparse
import shutil
import sys
import subprocess
from subprocess import check_call, check_output, CalledProcessError
#from wok.plugins.kimchi.config import  get_kimchi_version

REPOS_LIST     = ('production', 'staging')
DISTROS_LIST   = ('centos/8', 'fedora/31', 'ubuntu/19.10', 'debian/10', 'opensuse/15.1', 'all')
JFROG_BASE     = 'https://kimchi.jfrog.io/kimchi/'

COMMON_PACKAGES = [

    'gcc make autoconf automake git python3-pip python3-requests python3-mock \
    systemd logrotate python3-psutil python3-ldap python3-lxml python3-websockify \
    python3-jsonschema openssl nginx python3-configobj python3-lxml python3-magic \
    python3-paramiko python3-ldap spice-html5 novnc qemu-kvm'
    ] 

WOK = [
    'git clone https://github.com/kimchi-project/wok.git /var/wok',
    'sudo -H pip3 install -r /var/wok/requirements-dev.txt',
    ] 

KIMCHI = [
    'mkdir -p /var/wok/src/wok/plugins/kimchi/',
    'git clone https://github.com/kimchi-project/kimchi.git /var/wok/src/wok/plugins/kimchi/',
    'sudo -H pip3 install -r /var/wok/src/wok/plugins/kimchi/requirements-dev.txt',
    ]

PACKAGES           = {}
PACKAGES['wok']    = WOK
PACKAGES['kimchi'] = KIMCHI
BUILD              = [['./autogen.sh', '--system'], ['make'], ['make','install']]

COMMANDS_OS = {
    'debian' : { 
        'install' : 'apt install -y',
        'update' : 'apt update -y',
        'make' : ['make', 'deb'],
        'pk' : '.deb',
        'extra' : 'gettext pkgconf xsltproc python3-dev pep8 pyflakes python3-yaml python3-libvirt \
            python3-parted python3-guestfs python3-pil python3-cherrypy3 libvirt0 libvirt-daemon-system \
            libvirt-clients nfs-common sosreport open-iscsi libguestfs-tools libnl-route-3-dev',
        'pip' : 'sudo -H pip3 install -r /var/wok/src/wok/plugins/kimchi/requirements-UBUNTU.txt',
        },
    'fedora' : {
        'install' : '',
        'update' : '',
        'make' : "",
        'extra' : 'gettext-devel rpm-build libxslt gcc-c++ python3-devel python3-pep8 python3-pyflakes \
            rpmlint python3-pyyaml python3-libvirt python3-pyparted python3-ethtool python3-pillow \
            python3-cherrypy python3-libguestfs libvirt libvirt-daemon-config-network iscsi-initiator-utils \
            libguestfs-tools sos nfs-utils',
        'pip' : 'sudo -H pip3 install -r /var/wok/src/wok/plugins/kimch/requirements-FEDORA.txt',
    },
    'opensuse/LEAP' : {
        'install' : '',
        'update' : '',
        'make' : "",
        'extra': 'gettext-tools rpm-build libxslt-tools gcc-c++ python3-devel python3-pep8 python3-pyflakes \
            rpmlint python3-PyYAML python3-distro python3-libvirt-python python3-ethtool python3-Pillow \
            python3-CherryPy python3-ipaddr python3-libguestfs parted-devel libvirt \
            libvirt-daemon-config-network open-iscsi guestfs-tools nfs-client python3-devel',
        'pip' : 'sudo -H pip3 install -r /var/wok/src/wok/plugins/kimch/requirements-OPENSUSE-LEAP.txt',
    },
}

def usage():

    '''
    # Handle parameters

    @param repo string repository
    @param distro string distro
    @param user string JFROG user
    @param password string Token JFROG
    '''

    parser = argparse.ArgumentParser(
        description='python install.py -r production -d rhel/7 -u username -p password ',
    )

    parser.add_argument("-r", "--repo", choices=REPOS_LIST, required=True)
    parser.add_argument("-d", "--distro", choices=DISTROS_LIST, default="all")
    parser.add_argument("-u", "--user", help="Account name at %s. This account needs to be granted to write in \
        the repository." % (JFROG_BASE), metavar=("<username>"),required=True)
    parser.add_argument("-p", "--password", help="Token at %s. This token needs to be granted to write in."
            % (JFROG_BASE),metavar=("<password>"),required=True)
 
    args  = parser.parse_args()
    repo  = args.repo

    if args.distro == "all":
        distros = DISTROS_LIST
        distros.remove("all")
    else:
        distros = [args.distro]

    return repo, distros, args.user, args.password

def run_cmd(command):

    '''
    Run the given command using check_call and verify its return code.
    @param str command command to be executed
    '''

    try:
        check_call(command.split())
    except CalledProcessError as e:
        print('An exception h:as occurred: {0}'.format(e))
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
    try:
        build = subprocess.Popen(list, cwd=dir)
        build.wait()
    except CalledProcessError as e:
        print('An exception has occurred: {0}'.format(e))
        sys.exit(1)

def curl_cmd(distro_name, distro, package_name, user, password, path):
    '''
    Move package to JFROG repository
    @param str distro_name distro name
    @param str distro distro name and version
    @param str package_name package name
    @param str user JFROG user
    @param str password JFROG password
    @param str path path to package
    '''

    if distro_name == 'debian':
        cmd = 'curl -u%s:%s -XPUT "https://kimchi.jfrog.io/kimchi/%s/%s;deb.distribution=%s; \
            deb.component=kimchi;deb.architecture=noarch" -T %s' \
            % (user, password, distro, package_name, distro, path )
    else:
        cmd = 'curl -u%s:%s -XPUT https://kimchi.jfrog.io/kimchi/%s/ -T %s' % (user, password, distro, path)
    execute_cmd([cmd], 'Moving package to JFROG')

def main():
   

    repo, distros, user, password  = usage()
    #version = get_kimchi_version()
    version =  "3.0.0"
    release = "4.gitf3fbc1ea"

    for distro in distros:
        distro_name = distro.split("/")
        if distro_name[0] == 'ubuntu':
            pm = 'debian'
        else:
            pm = distro_name[0]

    '''
        try:
            shutil.rmtree('/var/wok/')
        except:
            pass
        
        execute_cmd([COMMANDS_OS[pm]['update']], 'Updating system')
        execute_cmd([COMMANDS_OS[pm]['install'] + ' ' + str(COMMON_PACKAGES[0])],
            'Intalling necessary basic Packages')
        execute_cmd([COMMANDS_OS[pm]['install'] + ' ' + COMMANDS_OS[pm]['extra']],
            'Intalling necessary extra Packages')
        execute_cmd(PACKAGES['wok'], 'Installing Wok')
        execute_cmd(PACKAGES['kimchi'], 'Installing Kimchi')
        execute_cmd([COMMANDS_OS[pm]['pip']],'Installin Pip packages') 
        
        for item in BUILD:
            
            run_build(item, '/var/wok/')
            run_build(item, '/var/wok/src/wok/plugins/kimchi/')
            
        run_build(COMMANDS_OS[pm]['make'], '/var/wok/')
        run_build(COMMANDS_OS[pm]['make'], '/var/wok/src/wok/plugins/kimchi/')
        '''
    wok_package    = 'wok-'    + version + '.' + release + '.' + distro_name[0] + '.noarch' + COMMANDS_OS[pm]['pk']
    kimchi_package = 'kimchi-' + version + '-' + release + '.noarch' + COMMANDS_OS[pm]['pk']
    
    #curl_cmd(distro_name[0], distro, wok_package, user, password, '/var/wok/' + wok_package)
    curl_cmd(distro_name[0], distro, wok_package, user, password, '/var/wok/src/wok/plugins/kimchi/' + kimchi_package)
    print("All Good, check JFROG")

if __name__ == "__main__":
    main()
