# First we import the Fabric api
from fabric.api import *
from fabric.contrib.project import rsync_project
from fabric.contrib.files import exists

# We can then specify host(s) and run the same commands across those systems
env.user = 'neumsequ'
env.hosts = ['cchumuser01.in2p3.fr']
env.key_filename = ['/home/raph/.ssh/id_rsa','/Users/philippe/.ssh/id_rsa']

def local_uname():
    local('uname -a')

def uname():
    run("uname -a")

@hosts([env.hosts[0]])
def deploy():
    # Sync the remote directory with the current project directory.
    excludelist=['.git',
                 'scorelib/local_settings.py',
                 'fabfile*',
                 ]

    rsync_project(local_dir='./', remote_dir='/sites/neumsequ/www/scorelib/',exclude=excludelist)

    # Activate the environment and install requirements
    #run('source path/to/project/bin/activate')
    #run('pip install -r path/to/project/requirements_file.txt')

    with cd('/sites/neumsequ/www/scorelib/'):
        # Collect all the static files
        #run('python manage.py collectstatic')

        # Migrate and Update the database
        run('python manage.py makemigrations')
        run('python manage.py migrate')
        run('python manage.py syncdb')

        run('touch /sites/neumsequ/www/scorelib/scorelib/wsgi.py')
