import os
import re
import MySQLdb
from classes import Env, RancherAPI

def environment_from_file(env_class_obj):
    if os.path.exists('.env'):
        x = open('.env', 'r')
        for i in x.read().split(sep='\n'):
            s = i.split(sep='=')
            if len(s) == 2:
                env_class_obj[s[0]] = env_class_obj[s[1].replace('\n','').replace('\r','')]
        x.close()
    return env_class_obj

def environment(env_class_obj):
    e = env_class_obj.env
    for i in os.environ:
        if i in e:
            e[i] = os.environ[i]
            continue
        x = re.match(r'MAIL_.*', i)
        if x:
            e[i] = os.environ[i]
            continue
        x = re.match(r'RANCHER_.*', i)
        if x:
            e[i] = os.environ[i]
            continue
    return env_class_obj

def create_database(database, env=None):
    conn = MySQLdb.connect(user=env['DB_ADMIN_USERNAME'],passwd=env['DB_ADMIN_PASSWORD'],host=env['DB_HOST'],port=env['DB_PORT'])
    c = conn.cursor()

    c.execute("CREATE DATABASE IF NOT EXISTS {} COLLATE = 'utf8_general_ci' CHARACTER SET = 'utf8'".format(database))
    c.execute("CREATE USER IF NOT EXISTS '{}'@'%' IDENTIFIED BY {}".format(database, database))
    c.execute("GRANT ALL ON {}.* TO '{}'@'localhost' IDENTIFIED BY {}".format(database, database, database))
    c.execute("GRANT ALL ON {}.* TO '{}'@'%' IDENTIFIED BY '{}".format(database, database, database))
    c.commit()
    c.close()
    conn.close()

def frormat_compose(str_obj, env=None):
    def regxp(s,env):
        for i in env:
            r = env[i]
            x = re.findall(i, s)
            if x and r:
                s = s.replace(x[0], r)
        return s

    x = [regxp(i, env) for i in str_obj.split(sep='\n')]
    return '\n'.join(x)

def create_stack(site_url, stack_name, env=None):
    def f_read(file):
        x = open(file, 'r')
        r = x.read()
        x.close()
        return r

    x = RancherAPI(key=env.env.get('RANCHER_API_KEY'), secret=env.env.get('RANCHER_API_SECRET'), base_url=env.env.get('RANCHER_API_URL'))
    x.environment['SITEURL'] = site_url
    x.set_project()
    x.dockercompose = frormat_compose(f_read('files/docker-compose.yaml'), env=env.env)
    x.ranchercompose = frormat_compose(f_read('files/rancher-compose.yaml'), env=env.env)
    x.name = stack_name
    x.create_stack()
    x.set_load_balancer()
    if x.loadbalancer: 
        x.set_service_id()
        x.register_lb()
    return (x.id, x.name)
