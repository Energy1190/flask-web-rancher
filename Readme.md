# Description #

This program is designed to register stack in the Rancher. Stacks are registered based on [docker-compose.yaml](app/files/docker-compose.yaml) and [rancher-compose.yaml](app/files/rancher-compose.yaml) files, with additional transfer of a number of variables from users.

# Installation #

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

###### Note ######

Variable `RANCHER_LB_NAME` specifies the name of the load balancer service, if this value is not specified, the program assumes that you have one balancer and uses it. If you have more than one balancer and this variable is not set, the program will not work.

Variable `RANCHER_SERVICE_NAME` specifies the name of the service d in the created stack that will be used on the load balancer, if this variable is not specified, the application assumes that you have one service in the created stack and uses it. If you have more than one service in the stack, and the variable is not defined, the application will not work.

Variables `DB_PORT` and `DB_ADMIN_USERNAME` are specified by the application by default `3306` and `root`. But you can change them if necessary.

# API

The application involves using the web interface, as well as addressing through software requests.

To access the application, you can use software tools such as `curl`. To receive a reply, you must pass a header `Accept: application/json`.

To get the list of stacks, you need to send a request:
- `curl -H "Accept: application/json" -X GET http://mgmt.webapp.appfurnish.com/`

For detailed information about the stack, you must send a request:

- `curl -H "Accept: application/json" -X GET http://mgmt.webapp.appfurnish.com/detail/<stack id>`

To delete the stack, you must send a request:

- `curl -H "Accept: application/json" -X GET http://mgmt.webapp.appfurnish.com/delete/<stack id>`

To add a stack, you must send a request:

- `curl -H "Accept: application/json" -d "site-url=<value>" -d "instance_name=<value>" -H "Content-Type: application/x-www-form-urlencoded" -X POST http://mgmt.webapp.appfurnish.com/add`
