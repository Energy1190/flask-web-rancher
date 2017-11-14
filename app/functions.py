import os
import re
import MySQLdb
import uuid
import yaml
from urllib.parse import urlparse
from classes import Env, RancherAPI
import markdown
import validators
import re

def environment(env_class_obj):
    e = env_class_obj.app_env
    for i in os.environ:
        if i in e:
            e[i] = os.environ[i]
        x = re.match(r'MAIL_.*', i)
        if x:
            e[i] = os.environ[i]
        x = re.match(r'RANCHER_.*', i)
        if x:
            e[i] = os.environ[i]
        if i == 'DB_HOST':
            env_class_obj.db_host_set = True
            env_class_obj.docker_env[i] = os.environ[i]
    return env_class_obj

def get_database_host(env_class_obj):
    if env_class_obj.db_host_set: return True

def create_database(env=None):
    database = env.docker_env['DB_DATABASE']
    user = env.docker_env['DB_USERNAME']
    passwd = env.docker_env['DB_PASSWORD']

    conn = MySQLdb.connect(user=env.app_env['DB_ADMIN_USERNAME'],passwd=env.app_env['DB_ADMIN_PASSWORD'],host=env.app_env['DB_HOST'],port=env.app_env['DB_PORT'])
    c = conn.cursor()

    c.execute("CREATE DATABASE IF NOT EXISTS {} COLLATE = 'utf8_general_ci' CHARACTER SET = 'utf8'".format(database))
    c.execute("CREATE USER IF NOT EXISTS '{}'@'%' IDENTIFIED BY '{}'".format(user, passwd))
    c.execute("GRANT ALL ON {}.* TO '{}'@'localhost' IDENTIFIED BY '{}'".format(database, user, passwd))
    c.execute("GRANT ALL ON {}.* TO '{}'@'%' IDENTIFIED BY '{}'".format(database, user, passwd))
    c.close()
    
    conn.commit()
    conn.close()

def frormat_compose(str_obj, env=None, service=None):
    def set_env(environment, env=None):
        if not environment: environment = {}
        for i in env:
            environment[i] = env[i]
        return environment

    x = yaml.load(str_obj)
    for i in x['services']:
        if not service or service and service == i:
            x['services'][i]['environment'] = set_env(x['services'][i].get('environment'), env=env)

    x = yaml.dump(x)
    return x

def delete_stack(stack_name, env=None):
    x = RancherAPI(key=env.app_env.get('RANCHER_API_KEY'), secret=env.app_env.get('RANCHER_API_SECRET'),
                   base_url=env.app_env.get('RANCHER_API_URL'))
    x.set_project()
    x.set_stack_id(name=stack_name)
    return x.remove_stack()

def create_stack(site_url, stack_name, env=None):
    def f_read(file):
        x = open(file, 'r')
        r = x.read()
        x.close()
        return r

    if not validators.url(site_url):
        return {'status': 400, 'code': 'Invalid URL format', 'type': 'error'}

    if not re.match(r'^[\w\d]+$', stack_name):
        return {'status': 400, 'code': 'Invalid Instance name', 'type': 'error'}

    env.docker_env['DB_USERNAME'] = stack_name + '_user'
    env.docker_env['DB_PASSWORD'] = str(uuid.uuid4())
    env.docker_env['DB_DATABASE'] = stack_name.replace('-', '_')

    x = RancherAPI(key=env.app_env.get('RANCHER_API_KEY'), secret=env.app_env.get('RANCHER_API_SECRET'), base_url=env.app_env.get('RANCHER_API_URL'))
    x.environment['SITEURL'] = site_url
    env.docker_env['SITE_URL'] = site_url
    x.set_project()
    if len(x.errordata): return x.errordata
    try:
        x.dockercompose = frormat_compose(f_read('files/docker-compose.yaml'), env=env.docker_env, service=env.app_env.get('RANCHER_ENVIRONMENT_NAME'))
    except:
        return {'status': 500, 'code': 'Yaml parsing error', 'type': 'error'}
    x.ranchercompose = f_read('files/rancher-compose.yaml')
    x.name = stack_name
    x.create_stack()
    if len(x.errordata):
        x.errordata['debug_detail'] = 'Create stack fail'
        return x.errordata
    x.set_load_balancer(name=env.app_env.get('RANCHER_LB_NAME'))
    if len(x.errordata):
        x.errordata['debug_detail'] = 'Set lb fail'
        return x.errordata

    if x.loadbalancer:
        x.set_service_id(name=env.app_env.get('RANCHER_SERVICE_NAME'))
        if len(x.errordata):
            x.errordata['debug_detail'] = 'Set serviceId fail'
            return x.errordata
        if not x.serviceid: return {'type': 'error', 'status': 500, 'code': 'Empty ServiceId, service was not created'}
        x.register_lb()
        if len(x.errordata):
            x.errordata['debug_detail'] = 'Register lb fail'
            return x.errordata
        x.lb = x.get_lb()
        [x.lb['lbConfig']['portRules'].append({'type': 'portRule', 'hostname': (urlparse(site_url).hostname or site_url), 'priority': 2, 'protocol': env.lb_env['protocol'], 'serviceId': x.serviceid, 'sourcePort': i[0], 'targetPort': i[1]})for i in env.lb_env['ports_map']]
        x.update_lb()
        if len(x.errordata):
            x.errordata['debug_detail'] = 'Update lb fail'
            return x.errordata
    return {'id': x.id, 'name': x.name, 'type': 'succsess'}

def conver_to_html():
    f = open('Readme.md', 'r')
    x = markdown.Markdown(output_format='html').convert(f.read())
    f.close()
    return x
