# Description

This program is designed to register stack in rancher. Stacks are registered based on `dokcer-compose.yaml` and `rancher-compose.yaml` files, with additional transfer of a number of variables from users.The application is located by default at 5000 port. 

# Installation

When the docker is launched, the container must have the following variables:

- `RANCHER_API_URL`
- `RANCHER_API_KEY`
- `RANCHER_API_SECRET`
- `DB_HOST`
- `DB_ADMIN_PASSWORD`

There also exist a number of optional variables:

- `RANCHER_LB_NAME`
- `RANCHER_SERVICE_NAME`
- `DB_ADMIN_USERNAME`
- `DB_PORT`

###### Note:
Variable `RANCHER_LB_NAME` specifies the name of the load balancer service, if this value is not specified, the program assumes that you have one balancer and uses it. If you have more than one balancer and this variable is not set, the program will not work.
Variable `RANCHER_SERVICE_NAME` specifies the name of the service d in the created stack that will be used on the load balancer, if this variable is not specified, the application assumes that you have one service in the created stack and uses it. If you have more than one service in the stack, and the variable is not defined, the application will not work.
Variables `DB_PORT` and `DB_ADMIN_USERNAME` are specified by the application by default `3306` and `root`. But you can change them if necessary.

# Customization

It is possible to customize the application by specifying its files `dokcer-compose.yaml` and `rancher-compose.yaml` this can be done at the start of the container: ` -v <path to file>:/app/file/docker-compose.yaml -v <path to file>:/app/file/rancher-compose.yaml`.

# Manual

The application involves using the web interface, as well as addressing through software requests.

### Web interface

On the main page, the application displays a list of all the stacks started by the application. At the top of the window there are links to the main stranger, a page with a form for adding a new stack and a link to this document.

To add a new stack, you need to go to the appropriate page `/add` and fill out the form. The form consists of two fields `Site URL` and `Instance name`. `Site URL` specifies the web address, and `Instance name` is used to select the name when creating the stack and the database. `Site URL` must be the correct url-address, otherwise the application will return an error, `Instance name` must match the requirements for names Myql, otherwise the application will return an error.

In order to remove the stack, you must click on `Delete` under the selected stack or open the page at `/delete/<stack id>`. To display detailed information about the stack, it is necessary to click on `Detail` under the selected stack or open the page at `/detail/<stack id>`.

### Api
To access the application, you can use software tools such as `curl`. To receive a reply, you must pass a header `Accept: application/json`.

To get the list of stacks, you need to send a request:
- `curl -H "Accept: application/json" -X GET <app base url>/`

For detailed information about the stack, you must send a request:

- `curl -H "Accept: application/json" -X GET <app base url>/detail/<stack id>`

To delete the stack, you must send a request:

- `curl -X GET <app base url>/delete/<stack id>`

To add a stack, you must send a request:

- `curl -d "site-url=<value>&instance_name=<value>" -H "Content-Type: application/x-www-form-urlencoded" -X POST <app base url>/add`
