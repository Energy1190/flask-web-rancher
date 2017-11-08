from flask import Flask, request, render_template, jsonify
from classes import RancherAPI, Env
from functions import environment, environment_from_file, create_stack, create_database

app = Flask(__name__)

envs = Env()
envs = environment_from_file(envs)
envs = environment(envs)

magic_list = ['id','name']

#envs.env['RANCHER_API_URL'] =
#envs.env['RANCHER_API_KEY'] =
#envs.env['RANCHER_API_SECRET'] =

def prepare_create(request):
    x = request.form.get('site-url')
    y = request.form.get('instance_name')
    if x and y:
        create_database(y, env=envs.env)
        create_stack(x,y, env=envs)

def query_args(func):
    def wrapper(*args, **kwargs):
        args_r = {}
        if request.method == 'GET':
            args_r = {i: request.args.get(i) for i in list(request.args)}
            if args_r.get('rancher-url'): envs.env['URL'] = args_r.get('rancher-url')
        if request.method == 'POST':
            prepare_create(request)
        x = func(*args, q_args=args_r, **kwargs)
        return x
    wrapper.__name__ = func.__name__
    return wrapper

@app.route("/", methods=['GET', 'POST'])
@query_args
def list_stack(q_args=None, **kwargs):
    if not envs.env.get('RANCHER_API_URL'): return render_template('get_url.html')
    r = RancherAPI(key=envs.env.get('RANCHER_API_KEY'), secret=envs.env.get('RANCHER_API_SECRET'), base_url=envs.env.get('RANCHER_API_URL'))
    r.set_project()
    stacks =[(i.get('id'), i.get('name'), envs.env['RANCHER_API_URL']) for i in r.get_stack_list().get('data') if i.get('group') == "io.rancher.service.create_by_app"]
    return render_template('stack_list.html', stacks=stacks, base_url=envs.env.get('RANCHER_API_URL'))

@app.route("/url", methods=['GET', 'POST'])
@query_args
def set_url(q_args=None, **kwargs):
    return render_template('get_url.html')

@app.route("/add", methods=['GET', 'POST'])
@query_args
def add_stack(q_args=None, **kwargs):
    return render_template('stack_add.html')

@app.route("/detail/<name>", methods=['GET'])
@query_args
def detail_stack(name, q_args=None, **kwargs):
    if not envs.env.get('RANCHER_API_URL'): return render_template('get_url.html')
    r = RancherAPI(key=envs.env.get('RANCHER_API_KEY'), secret=envs.env.get('RANCHER_API_SECRET'), base_url=envs.env.get('RANCHER_API_URL'))
    r.set_project()
    detail = [i for i in r.get_stack(name) if i in magic_list]
    return render_template('stack_detail.html', stack=r, detail=detail)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)