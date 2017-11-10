from flask import Flask, request, render_template, jsonify, Response
from classes import RancherAPI, Env
from functions import environment, create_stack, create_database
from functions import delete_stack as del_stack

app = Flask(__name__)

envs = Env()
envs = environment(envs)

magic_list = ['id','name', 'environment']

#envs.env['RANCHER_API_URL'] =
#envs.env['RANCHER_API_KEY'] =
#envs.env['RANCHER_API_SECRET'] =

def prepare_create(request):
    error = {'type': 'succsess'}
    x = request.form.get('site-url')
    y = request.form.get('instance_name')
    if x and y:
        try:
            create_database(y, env=envs)
        except:
            pass
            #error = {'type': 'error', 'status': 500, 'code': 'Database was not created'}
        if error.get('type') == 'error': return Response(response=str(error.get('status')) + ' ' + error.get('code'),
                                                         status=error.get('status'))
        error = create_stack(x,y, env=envs)
        if error.get('type') == 'error': return Response(response=str(error.get('status')) + ' ' + error.get('code'),
                                                         status=error.get('status'))

def query_args(func):
    def wrapper(*args, **kwargs):
        args_r = {}
        if request.method == 'GET':
            args_r = {i: request.args.get(i) for i in list(request.args)}
            if args_r.get('rancher-url'): envs.env['RANCHER_API_URL'] = args_r.get('rancher-url')
        if request.method == 'POST':
            x = prepare_create(request)
            if not x: x = list_stack(q_args=args_r, **kwargs)
        else:
            x = func(*args, q_args=args_r, **kwargs)
        return x
    wrapper.__name__ = func.__name__
    return wrapper

@app.route("/", methods=['GET', 'POST'])
@query_args
def list_stack(q_args=None, **kwargs):
    if not envs.app_env.get('RANCHER_API_URL'): return render_template('get_url.html')
    r = RancherAPI(key=envs.app_env.get('RANCHER_API_KEY'), secret=envs.app_env.get('RANCHER_API_SECRET'), base_url=envs.app_env.get('RANCHER_API_URL'))
    r.set_project()
    stacks =[(i.get('id'), i.get('name'), envs.app_env['RANCHER_API_URL']) for i in r.get_stack_list().get('data') if i.get('group') == "io.rancher.service.create_by_app"]
    return render_template('stack_list.html', stacks=stacks, base_url=envs.app_env.get('RANCHER_API_URL'))

@app.route("/add", methods=['GET', 'POST'])
@query_args
def add_stack(q_args=None, **kwargs):
    return render_template('stack_add.html')

@app.route("/detail/<name>", methods=['GET'])
@query_args
def detail_stack(name, q_args=None, **kwargs):
    if not envs.app_env.get('RANCHER_API_URL'): return render_template('get_url.html')
    r = RancherAPI(key=envs.app_env.get('RANCHER_API_KEY'), secret=envs.app_env.get('RANCHER_API_SECRET'), base_url=envs.app_env.get('RANCHER_API_URL'))
    r.set_project()
    x = r.get_stack(name)
    detail = {i:x[i] for i in x if i in magic_list}
    return render_template('stack_detail.html', stack=r, detail=detail)

@app.route("/delete/<name>", methods=['GET'])
@query_args
def delete_stack(name, q_args=None, **kwargs):
    x = del_stack(name, env=envs)
    if x.get('type') == 'error':
        return Response(response=str(x.get('status')) + ' ' + x.get('code'),
                                                         status=x.get('status'))
    else:
        return list_stack()
    
@app.route("/help/", methods=['GET'])
@query_args
def help_me(q_args=None, **kwargs):
    return Response(response='Help here!', status=200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
