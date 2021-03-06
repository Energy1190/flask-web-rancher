from flask import Flask, request, render_template, jsonify, Response
from classes import RancherAPI, Env
from functions import environment, create_stack, create_database, conver_to_html, get_database_host
from functions import delete_stack as del_stack
from werkzeug.serving import run_simple

app = Flask(__name__)

envs = Env()
envs = environment(envs)
get_database_host(envs)

magic_list = ['id','name', 'environment']

def prepare_create(request):
    baseerror = {'type': 'succsess'}
    stackerror = {'type': 'succsess'}

    x = request.form.get('site-url')
    y = request.form.get('instance_name')
    if x and y:
        stackerror = create_stack(x,y, env=envs)
        if stackerror.get('type') == 'error': return Response(response=str(stackerror.get('status')) + ' ' + stackerror.get('code'),
                                                         status=stackerror.get('status'))
        try:
            create_database(env=envs)
        except:
            baseerror = {'type': 'error', 'status': 500, 'code': 'Database was not created'}
        if baseerror.get('type') == 'error':
            del_stack(stackerror.get('id'), env=envs)
            return Response(response=str(baseerror.get('status')) + ' ' + baseerror.get('code'),
                                                         status=baseerror.get('status'))

def query_args(func):
    def wrapper(*args, redirected=False, **kwargs):
        args_r = {}
        if request.method == 'GET':
            args_r = {i: request.args.get(i) for i in list(request.args)}
            if args_r.get('rancher-url'): envs.env['RANCHER_API_URL'] = args_r.get('rancher-url')
            if 'application/json' in request.headers['Accept'].split(sep=' '): kwargs['answ_json'] = True
        if request.method == 'POST' and not redirected:
            x = prepare_create(request)
            if not x:
                return list_stack(redirected=True, **kwargs)
        else:
            x = func(*args, q_args=args_r, **kwargs)
        return x
    wrapper.__name__ = func.__name__
    return wrapper

@app.route("/", methods=['GET', 'POST'])
@query_args
def list_stack(q_args=None, answ_json=False, **kwargs):
    r = RancherAPI(key=envs.app_env.get('RANCHER_API_KEY'), secret=envs.app_env.get('RANCHER_API_SECRET'), base_url=envs.app_env.get('RANCHER_API_URL'))
    r.set_project()
    stacks =[(i.get('id'), i.get('name'), i.get('environment').get('SITEURL')) for i in r.get_stack_list().get('data') if i.get('group') == "io.rancher.service.create_by_app"]
    if answ_json: return jsonify(stacks)
    return render_template('stack_list.html', stacks=stacks, base_url=envs.app_env.get('RANCHER_API_URL'))

@app.route("/add", methods=['GET', 'POST'])
@query_args
def add_stack(q_args=None, **kwargs):
    return render_template('stack_add.html')

@app.route("/detail/<name>", methods=['GET'])
@query_args
def detail_stack(name, q_args=None, answ_json=False, **kwargs):
    r = RancherAPI(key=envs.app_env.get('RANCHER_API_KEY'), secret=envs.app_env.get('RANCHER_API_SECRET'), base_url=envs.app_env.get('RANCHER_API_URL'))
    r.set_project()
    x = r.get_stack(name)
    detail = {i:x[i] for i in x if i in magic_list}
    if answ_json: return jsonify((r, detail))
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
    x = conver_to_html()
    return render_template('help.html', help_me=x)

if __name__ == "__main__":
    #app.run(host="0.0.0.0", port=5000, processes=5)
    run_simple('0.0.0.0', 5000, app, threaded=True)
