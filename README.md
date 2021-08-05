# guts-test
This is a repo for codes and deployment for the guts-test assignment.

## Introduction
This task requires deploying two instances of an API application to handle the designed API requests. The API application should be trivially easy to deploy on either AWS, k8s, any linux VM. Thus, the API application will be packaged into a docker image and can be deployed anywhere with docker installed. In this project, I will demostrate how to deploy the application container in docker-compose and docker swarm, as well as Kubernetes. The monitoring and log collection tool will also be provided for this deployment.

<img src="https://github.com/wqhuang-ustc/guts-test/blob/main/guts-demo-image.png" width="800">

## Implementation of API application

### Database and the sample dataset
To make the development moving fast, a MongoDB database will be installed in the EC2 server and initialized with a [Sample Supply Store Dataset](https://docs.atlas.mongodb.com/sample-data/sample-supplies/). This sample_supplies database contains data from a mock office supply company. The company tracks customer information and sales data, and has several store locations throught the world.

Follow the [official Mongodb guide](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/) to install the Mongodb in the EC2 instance. After finishing the installation, modify the bindIp in /etc/mongo.conf from 127.0.0.1(localhost) to the ips where you raise the connection to the db (0.0.0.0 to accept from any ip, convinient for development but not secure).

Init the Mongodb with a json file named [sales.json](sales.json) using the following command:
```
## create a new database for the imported json data
mongosh
    use mydb;
    exit;
mongoimport --db mydb --collection sales --file sales.json
## validate the imported data in Mongodb
mongosh
    use mydb;
    db.sales.find();
```
Now, the Mongodb is ready to accept query from our API application.

### API applicaiton

This API application is implemented using python flask. Take a look at the [api.py](app_dockerfile/api.py). And its api calls are protected by Flask-JWT token. To access the data in the database, you need to POST to get a token that will be used in your request to get data.
```
POST /auth HTTP/1.1
Host: ec2-13-53-186-244.eu-north-1.compute.amazonaws.com:5000
Content-Type: application/json
Content-Length: 60

{
    "username": "weiqing",
    "password": "happycoding"
}
```
The response should look similar to:
```
HTTP/1.1 200 OK
Content-Type: application/json

{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGl0eSI6MSwiaWF0IjoxNjI4MTY4OTg1LCJuYmYiOjE2MjgxNjg5ODUsImV4cCI6MTYyODE2OTI4NX0.XB8L7pJsekKOZJQgb0aDaEuIXImbU8pTDr58mgDtrb8"
}
```
This JWT token will be valid for 300 seconds. You will need to get a new token again after its expiration.You can validate this token by make a request to /protected as follow:
```
GET /protected HTTP/1.1
Host: ec2-13-53-186-244.eu-north-1.compute.amazonaws.com:5000
Authorization: JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGl0eSI6MSwiaWF0IjoxNjI4MTcyOTIxLCJuYmYiOjE2MjgxNzI5MjEsImV4cCI6MTYyODE3MzIyMX0.-rmO0udnw6b7hemqfQ9f1xppnt1YHPFilv4wEAmMr50
```
The response should look similar to:
```
HTTP/1.1 200 OK

User(id='1')
```

Now, you are ready to get all sales data from the Mongodb database via /api/v1/sales/all. 
```
GET /api/v1/sales/all HTTP/1.1
Host: ec2-13-53-186-244.eu-north-1.compute.amazonaws.com:5000
Authorization: JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGl0eSI6MSwiaWF0IjoxNjI4MTcyOTIxLCJuYmYiOjE2MjgxNzI5MjEsImV4cCI6MTYyODE3MzIyMX0.-rmO0udnw6b7hemqfQ9f1xppnt1YHPFilv4wEAmMr50
Content-Type: application/json
```
And you will get response like below:
```
{
    "customer": {
        "satisfaction": 4,
        "gender": "M",
        "age": 42,
        "email": "cauho@witwuta.sv"
    },
    "purchaseMethod": "Online",
    "couponUsed": true,
    "items": [
        {
            "price": {
                "$numberDecimal": "40.01"
            },
            "quantity": 2,
            "name": "printer paper",
            "tags": [
                "office",
                "stationary"
            ]
        },
        .....
        .....
}
```

This API application can be further extended to perform complicated query to the Mongodb, for example, find all sales in storeLocation: London and calculate the total price. But since this is a project for a DevOps Engineer, I will not implement these possible features.

### Containerization
To make it easy to deploy anywhere, let's containerize this API application with below command:
```
cd app_dockerfile
docker build . -t weiqinghuang/guts_api_demo:latest
# Push the image to my docker hub for the deployment in the EC2
docker push weiqinghuang/guts_api_demo:latest
```
Upon running, this API guts_api_demo container will run the api.py to put the application up on container port 5000.

### Deployment using docker-compose and docker swarm
Compose is a tool for defining and running multi-container Docker applications. With Compose, you use a YAML file to configure your application’s services. Then, with a single command, you create and start all the services from your configuration. Install the [Docker Engineer](https://docs.docker.com/engine/install/ubuntu/) and [docker-compose](https://docs.docker.com/compose/install/) in the EC2 instance so that we can launce the API application container via docker-compose command.
```
cd /direcotry/to/docker-compose.yml
docker-compose up -d
```

API application deployed by docker-compose is located in a single VM, and cannot survive single node failure, also, there exist some down time while deploying a new version of the application. To overcome above problem, we can use docker swarm to provide advanced rolling update stragety and high available swarm cluster, which consists of multiple Docker hosts. In this project, I will create a single node swarm cluster and deploy the API application into it.

On the EC2 instance, run docker `swarm init` to create a single-node swarm. The output will look like below:
```
Swarm initialized: current node (ptxeo5d0xps28dtfyadyw0ico) is now a manager.

To add a worker to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-1bw6xg1su3nu3aupvxlivkseduunr0h7ysog1b9gkk60ak55pj-5xq4xu4cjtbmdinfekl723xue 172.31.4.19:2377

To add a manager to this swarm, run 'docker swarm join-token manager' and follow the instructions.
```
To create a multi-nodes swarm cluster for preventing single node failure, follow the official guide: [Getting started with swarm mode](https://docs.docker.com/engine/swarm/swarm-tutorial/).

Now, we can deploy/update the API application in the single-node swarm cluster using the following command:
```
docker stack deploy --compose-file docker-compose.yml gutsdemo
```
Modify the [docker-compose.yml](docker-compose.yml) for advance deployment strategy.
1. Modify the replicas from 1 to 2 to get 2 replicas of the API application instance.
2. Add parallelism: 1 under update_config to update the deployment one by one for zero downtime.
3. Add on-failure restart_policy to restart the container when the container failed and exited

To delete the API application from the swarm, run below command:
```
docker stack rm gutsdemo
```

### Deployment in Kubernetes cluster