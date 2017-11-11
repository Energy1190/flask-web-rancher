import uuid
import json
import time
import requests
from requests.auth import HTTPBasicAuth

class Env():
    app_env = {'RANCHER_LB_NAME': None, 'DB_HOST': '127.0.0.1', 'DB_PORT': 3306, 'DB_ADMIN_USERNAME': 'root', 'DB_ADMIN_PASSWORD': None,
               'RANCHER_API_URL': None, 'RANCHER_API_KEY': False, 'RANCHER_API_SECRET': False}

    docker_env = {'DB_HOST': '127.0.0.1', 'DB_PORT': 3306, 'DB_USERNAME': None, 'DB_PASSWORD': None, 'DB_DATABASE': None,
                  'SITE_URL': None}

    lb_env = {'protocol': 'http', 'ports_map': [(80, 80)]}

    db_host_set = False

class RancherAPI():
    def __init__(self, key=None, secret=None, base_url=None):
        self.project = None
        self.loadbalancer = None

        self.key = key
        self.secret = secret
        self.base_url = base_url

        assert base_url
        self._test()
        self.project_list = [i.get('id') for i in self.get_project_list().get('data')]

        self.name = None
        self.id = None
        self.serviceid = None
        
        self.dockercompose = None
        self.ranchercompose = None
        self.description = None
        self.environment = {'APP_URL': None}
        self.group = "io.rancher.service.create_by_app"
        self.startOnCreate = True

        self.data = {}
        self.errordata = {}
        self.lb = {}

    def error(func):
        def wrap(self, *args, **kwargs):
            x = func(self, *args, **kwargs)
            if x.get('type') == 'error':
                self.errordata = x
            else:
                self.errordata = {}
            return x
        return wrap

    def auth(func):
        def wrap(self, *args, **kwargs):
            if self.key and self.secret: x = func(self, auth=HTTPBasicAuth(self.key, self.secret), *args, **kwargs)
            else: x = func(self, *args, **kwargs)
            return x
        return wrap

    def post_processing(func):
        def wrap(self, *args, **kwargs):
            x = func(self, *args, **kwargs)
            if x.get('id'): self.id = x.get('id')
            if x.get('name'): self.name = x.get('name')
            return x
        return wrap

    @auth
    @error
    def _test(self, **kwargs):
        try:
            x = requests.get(self.base_url + '/v2-beta', **kwargs)
        except:
            return {'type': 'error', 'status': 1, 'code': 'Failed to connect', 'message': 'Failed to connect'}
        return x.json()

    @auth
    @error
    def get_stack_list(self, **kwargs):
        assert self.project
        x = requests.get(self.base_url + '/v2-beta/projects/{}/stacks'.format(self.project), **kwargs)
        return x.json()

    @auth
    @error
    def get_project_list(self, **kwargs):
        x = requests.get(self.base_url + '/v2-beta/projects', **kwargs)
        return x.json()

    @auth
    @error
    def get_load_balancer_list(self, **kwargs):
        assert self.project
        x = requests.get(self.base_url + '/v2-beta/projects/{}/loadbalancerservices'.format(self.project), **kwargs)
        return x.json()

    @auth
    @error
    def get_service_list(self, **kwargs):
        assert self.project
        assert self.id
        x = requests.get(self.base_url + '/v2-beta/projects/{}/stacks/{}/services'.format(self.project, self.id), **kwargs)
        return x.json()

    def set_project(self, name=None):
        if not name and len(self.get_project_list()['data']) == 1:
            self.project = self.get_project_list()['data'][0]['id']
        else:
            self.project = name

    def set_load_balancer(self, name=None, id=None):
        if not name and not id and len(self.get_load_balancer_list()['data']) == 1:
            self.loadbalancer = self.get_load_balancer_list()['data'][0]['id']
        elif id:
            self.loadbalancer = id
        elif name:
            x =[i['id'] for i in self.get_load_balancer_list()['data'] if i['name'] == name]
            if len(x) == 1: self.loadbalancer = x[0]

    def set_stack_id(self, name=None):
        if not name and len(self.get_stack_list()['data']) == 1:
            self.id = self.get_stack_list()['data'][0]['id']
        else:
            self.id = name

    def set_service_id(self, name=None, id=None, r=False):
        if not name and not id and len(self.get_service_list()['data']) == 1:
            self.serviceid = self.get_service_list()['data'][0]['id']
            if self.serviceid: return True
        elif id:
            self.serviceid = id
            if self.serviceid: return True
        elif name:
            x =[i['id'] for i in self.get_service_list()['data'] if i['name'] == name]
            if len(x) == 1:
                self.serviceid = x[0]
                if self.serviceid: return True
        if not r:
            time.sleep(5)
            self.set_service_id(name=name, id=id, r=True)

            
    def set_data(self):
        self.data['type'] = 'stack'
        self.data['name'] = (self.name or "Unknown-stack")
        self.data['description'] = (self.description or "No description")
        self.data['group'] = self.group
        self.data['environment'] = self.environment
        self.data['startOnCreate'] = self.startOnCreate
        if self.dockercompose: self.data['dockerCompose'] = self.dockercompose
        if self.ranchercompose: self.data['rancherCompose'] = self.ranchercompose

    @auth
    @error
    @post_processing
    def create_stack(self, **kwargs):
        assert self.project
        self.set_data()
        x = requests.post(self.base_url  + '/v2-beta/projects/{}/stacks'.format(self.project), data=json.dumps(self.data), **kwargs)
        return x.json()

    @auth
    @error
    def remove_stack(self, **kwargs):
        assert self.project
        assert self.id
        x = requests.delete(self.base_url  + '/v2-beta/projects/{}/stacks/{}'.format(self.project, self.id), **kwargs)
        return x.json()

    @auth
    @error
    def update_stack(self, **kwargs):
        assert self.project
        assert self.id
        self.set_data()
        x = requests.put(self.base_url  + '/v2-beta/projects/{}/stacks/{}'.format(self.project, self.id), data=self.data, **kwargs)
        return x.json()

    @auth
    @error
    @post_processing
    def get_stack(self, id, **kwargs):
        assert self.project
        x = requests.get(self.base_url  + '/v2-beta/projects/{}/stacks/{}'.format(self.project, id), **kwargs)
        r = x.json()
        if r.get('group') == "io.rancher.service.create_by_app": return r

    @auth
    @error
    def register_lb(self, **kwargs):
        assert self.project
        assert self.loadbalancer
        assert self.serviceid
        data = {"serviceLink": {"name":self.name + '_lb', "serviceId": self.serviceid, "uuid": str(uuid.uuid4())}}
        x = requests.post(self.base_url + '/v2-beta/projects/{}/loadbalancerservices/{}/?action=addservicelink'.format(self.project, self.loadbalancer), data=json.dumps(data), **kwargs)
        return x.json()

    @auth
    @error
    def get_lb(self, **kwargs):
        assert self.project
        assert self.loadbalancer
        x = requests.get(self.base_url + '/v2-beta/projects/{}/loadbalancerservices/{}'.format(self.project, self.loadbalancer), **kwargs)
        return x.json()

    @auth
    @error
    def update_lb(self, **kwargs):
        assert self.project
        assert self.loadbalancer
        assert self.lb
        data = self.lb
        x = requests.put(self.base_url + '/v2-beta/projects/{}/loadbalancerservices/{}'.format(self.project, self.loadbalancer), data=json.dumps(data), **kwargs)
        return x.json()
