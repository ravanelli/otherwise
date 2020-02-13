import shutil
import argparse
import sys
import subprocess
from subprocess import check_call, check_output, CalledProcessError
from ast import literal_eval
sys.path.append('/var/wok/src/wok/plugins/kimchi/config.py.in')


REPOS_LIST     = ('production', 'staging')
ARCHS_LIST     = ['x86', 'ppc64le', 'noarch', 'all']
STEPS_LIST     = ['1', '2', 'both']
DISTROS_LIST   = ['centos/10', 'fedora/31', 'rhel/7', 'rhel/8', 'sles/12', 'sles/15',
                  'ubuntu/19.10', 'debian/10', 'opensuse/15.1', 'all']
JFROG_BASE      = 'https://kimchi.jfrog.io/kimchi/'

debian_packages = [
    'apt update -y',
    'apt install -y gcc make autoconf automake git python3-pip python3-requests python3-mock \
    systemd logrotate python3-psutil python3-ldap python3-lxml python3-websockify \
    python3-jsonschema openssl nginx python3-cherrypy3 python3-cheetah python3-pampy \
    python-m2crypto gettext python3-openssl pkgconf xsltproc pep8 pyflakes python3-yaml \
    libnl-route-3-dev python3-configobj python3-magic python3-paramiko spice-html5 novnc \
    qemu-kvm python3-libvirt python3-parted python3-guestfs python3-pil libvirt0 \
    libvirt-daemon-system libvirt-clients nfs-common sosreport open-iscsi libguestfs-tools bc'
    ]

debian_wok = [
    'git clone https://github.com/kimchi-project/wok.git /var/wok',
    'sudo -H pip3 install -r /var/wok/requirements-dev.txt',
    'mkdir -p /var/wok/src/wok/plugins/kimchi/',
    'git clone https://github.com/kimchi-project/kimchi.git /var/wok/src/wok/plugins/kimchi/',
    'sudo -H pip3 install -r /var/wok/src/wok/plugins/kimchi/requirements-dev.txt',
    'sudo -H pip3 install -r /var/wok/src/wok/plugins/kimchi/requirements-UBUNTU.txt'
    ]

packages = {}
packages['debian_packages'] = debian_packages
packages['debian_wok'] = debian_wok
build = [['./autogen.sh', '--system'], ['make'], ['make','install']]

def usage():

    '''
    # Handle parameters

    @param step string steps to run
    @param repo string repository
    @param distro string distro
    @param arch string architecture
    @param user string JFROG user
    @param password string Token JFROG
    @param path string path to folder/package
    '''

    parser = argparse.ArgumentParser(
        description='python install.py -s both -r production -d rhel/7 -a noarch -pa mydir -u username -p password ',
    )

    parser.add_argument("-s", "--step", choices=STEPS_LIST, required=True)
    parser.add_argument("-r", "--repo", choices=REPOS_LIST, required=True)
    parser.add_argument("-d", "--distro", choices=DISTROS_LIST, default="all")
    parser.add_argument("-a", "--arch", choices=ARCHS_LIST, default="all")
    parser.add_argument("-pa", "--path")
    parser.add_argument("-u", "--user", help="Account name at %s. This account needs to be granted to write in the repository." 
        % (JFROG_BASE), metavar=("<username>"),required=True)
    parser.add_argument("-p", "--password", help="Token at %s. This token needs to be granted to write in." % (JFROG_BASE),
        metavar=("<password>"),required=True)
 
    args = parser.parse_args()
    repo    = args.repo
    steps       = []

    if args.step == "both":
        steps.append("1")
        steps.append("2")
    else:
        steps.append(args.step)

    if args.arch == "all":
        archs = ARCHS_LIST
        archs.remove("all")
    else:
        archs = [args.arch]

    if args.distro == "all":
        distros = DISTROS_LIST
        distros.remove("all")
    else:
        distros = [args.distro]

    return repo, steps, archs, distros, args.user, args.password

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
        print(item)
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
    Move package to JFROG
    @param str distro_name distro name
    @param str distro distro name and version
    @param str package_name package name
    @param str user JFROG user
    @param str password JFROG password
    @param str path path to package
    '''



    print(distro_name)
    if distro_name == 'debian':
        cmd = 'curl -u%s:%s -XPUT "https://kimchi.jfrog.io/kimchi/%s/%s;deb.distribution=%s;deb.component=kimchi;deb.architecture=noarch" -T %s' % (user, password, distro, package_name, distro, path )
    else:
        cmd = 'curl -u%s:%s -XPUT https://kimchi.jfrog.io/kimchi/%s/ -T %s' % (user, password, distro, path)
    print(cmd)
    execute_cmd(cmd, 'Moving package to JFROG')

def main():
   

    repo, steps, archs, distros, user, password  = usage()
    make_package = ['make', 'rpm']
    #version = get_kimchi_version()  todo
    version = '3.0.0'
    wok_package = 'wok-' + version  
    kimchi_package = ''

    #wok-3.0.0-1.gitae24f735.debian.noarch.deb
    
    for distro in distros:
        distro_name = distro.split("/")
        if distro_name[0] == 'ubuntu':
            wok_package += '.' + distro_name[0] + '.noarch.deb'
            distro_name[0] = 'debian'
            make_package = ['make', 'deb']
        else:
            wok_package = '.' + distro_name[0] + '.noarch.rpm'

        install_packages = distro_name[0] + '_packages'
        install_work = distro_name[0] + '_wok'

        #try:
        #    shutil.rmtree('/var/wok/')
        #except:
        #    pass

        #execute_cmd(packages[install_packages], 'Intalling necessary Packages')
        #execute_cmd(packages[install_work], 'Installing Wok and Kimchi')

        #for item in build:
        #    run_build(item, '/var/wok/')
        #    run_build(make_package, '/var/wok/')
       
        curl_cmd(distro_name[0], distro, wok_package, user, password, "/var/wok/wok-3.0.0*")
    
    print("All Good, Welcome to Kimchi")

if __name__ == "__main__":
    main()
