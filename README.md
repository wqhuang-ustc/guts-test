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

## Deployment of the API application

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

## Launch Kubernetes cluster and deploy API application

### Kubernetes nodes provisioning
I prefer provisioning Virtual Machines(VMs) using Infrastructure as Code(IaC). IaC manages infrastructures(virtual machine, networks, disks etc.) in a declarative way with the configuration file, it allows you to build, change and manage your infrastructure in a safe, consistent, repeatable way.

For this assignment, I will use Vagrant to create 3 Kubernetes nodes and configure them to satisfy the requirements of being a Kubernetes node. Vagrant is an ideal tool to create VMs for the development environment and you may use Terraform for provisioning VMs in a production environment. Check this [repo](https://github.com/wqhuang-ustc/terraform-kvm) for creating VMs using Terraform.

### Installation of Vagrant and VirtualBox
I use Vagrant version 2.2.16 and VirtualBox 6.1 on my MacOS. For Vagrant installation, check this [link](https://www.vagrantup.com/downloads). Use this [link](https://www.virtualbox.org/wiki/Downloads) to install VirtualBox in your environment.

### Configure VMs in the Vagrantfile and build
Modify this Vagrantfile under the kubespray directory to further customize the VMs.
1. $vm_memory (Increase to 4096M because Elasticsearch instance has minimum 2G memory requirement)
2. $subnet ||= "172.18.8" (Make sure this subnet is not already in use in your environment, change it if needed)
3. $os ||= "ubuntu1804" (Change this if you prefer other OS)

Run the below commands to launch VMs for the Kubernetes cluster:
```
git clone https://github.com/kubernetes-sigs/kubespray.git
cd kubespray
git checkout tags/v2.16.0
vagrant up --provider=virtualbox
```

### Deploy the Kubernetes via Kubespray
Kubespray is a composition of Ansible playbooks, inventory, provisioning tools, and domain knowledge for generic Kubernetes cluster configuration management tasks. Kubespray provides:
* A highly available cluster
* Composable attributes(Choice of the network plugin for instance)
* Support for most popular Linux distributions
* Can be run on bare metal and most cloud

1. **Install [python/python3](https://linuxize.com/post/how-to-install-python-3-7-on-ubuntu-18-04/) and [pip/pip3](https://linuxize.com/post/how-to-install-pip-on-ubuntu-18.04/) in your Ansible control machine.**

2. **CLone the Kubespray git repository into the control machine.**
    ```
    sudo apt-get install git -y
    git clone https://github.com/kubernetes-sigs/kubespray.git
    git checkout tags/v2.16.0  #For installing Kubernetes 1.20 
    ```
3. **Go to the Kubespray directory and install all dependency packages from "requirements.txt"(ansible, jinja2, netadd, pbr, hvac, jmespath, ruamel,yaml, etc.).**
   ```
   sudo pip install -r requirements.txt
   ```
4. **Update the Ansible inventory file using the info of VMs created above**
   Vagrant will generate the inventory automatically while launching the VMs in `.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory`, check this inventory and confirm the details of each node, update it if necessary.
5. **Review and modify parameters under "inventory/sample/group_vars" according to your environment and requirements**
   ```
   vim inventory/sample/group_vars/all/all.yml
   vim inventory/sample/group_vars/k8s-cluster/k8s-cluster.yml
   ```
6. **Deploy Kubespray with Ansible Playbook**
   ```
   ansible-playbook -vvv -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory cluster.yml
   ```
   Or use the Ansible provisioner in the Vagrantfile to launch the Kubernetes after creating all VMs successfully by uncommnet the last part of the Vagrantfile and run `Vagrant up`.
   ```
      # # Only execute the Ansible provisioner once, when all the machines are up and ready.
      # if i == $num_instances
      #   node.vm.provision "ansible" do |ansible|
      #     ansible.playbook = $playbook
      #     $ansible_inventory_path = File.join( $inventory, "hosts.ini")
      #     if File.exist?($ansible_inventory_path)
      #       ansible.inventory_path = $ansible_inventory_path
      #     end
      #     ansible.become = true
      #     ansible.limit = "all,localhost"
      #     ansible.host_key_checking = false
      #     ansible.raw_arguments = ["--forks=#{$num_instances}", "--flush-cache", "-e ansible_become_pass=vagrant"]
      #     ansible.host_vars = host_vars
      #     #ansible.tags = ['download']
      #     ansible.groups = {
      #       "etcd" => ["#{$instance_name_prefix}-[1:#{$etcd_instances}]"],
      #       "kube_control_plane" => ["#{$instance_name_prefix}-[1:#{$kube_master_instances}]"],
      #       "kube_node" => ["#{$instance_name_prefix}-[1:#{$kube_node_instances}]"],
      #       "k8s_cluster:children" => ["kube_control_plane", "kube_node"],
      #     }
      #   end
      # end
   ```
7. **Access k8s cluster viakubectl from the console by copy the /etc/kubernetes/admin.conf file to $HOME/.kube/config in the master node.**  
    
    ```
    vagrant ssh k8s-1
    mkdir -p $HOME/.kube; sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    sudo chown $(id -u):$(id -g) $HOME/.kube/config
    ```
    Verify kubectl is working by:  
    ```
    kubectl get nodes
    kubectl cluster-info
    ```
    To access the k8s cluster from your local machine, copy the contents of the /etc/kubernetes/admin.conf file into $HOME/.kube/config file in your machine.
    By default, kubectl looks for a file named config in the $HOME/.kube directory. You can specify other kubeconfig files by setting the KUBECONFIG environment variable or by setting the --kubeconfig=/path/to/your-config flag. If you are managing multiple Kubernetes cluster in your local environment, use contexts to control the access of multiple Kubernetes cluster.
    ```
    export KUBECONFIG=$KUBECONFIG:$HOME/.kube/guts-config
    kubectl config get-contexts
    kubectl config use-context guts-kubernetes-admin@guts-cluster
    ```

### Kubernetes dashboard
A Kubernetes dashboard will be deployed into the cluster first to provide a web-based UI for this Kubernetes clusters. It allows users to manage applications running in the cluster and troubleshoot them, as well as manage the cluster itself.  
To install the Dashboard, execute the following command:
```
kubectl apply -f k8s-dashboard/k8s-dashboard.yaml
kubectl apply -f k8s-dashboard/dashboard-adminuser.yaml
```

To access the Dashboard locally, Create a secure channel to the Kubernetes cluster.
```
kubectl proxy
```
Now access Dashboard at `http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/`. Find the token we can use to log in by running following command:
```
kubectl -n kubernetes-dashboard get secret $(kubectl -n kubernetes-dashboard get sa/admin-user -o jsonpath="{.secrets[0].name}") -o go-template="{{.data.token | base64decode}}"
```

### Deploy API application in the Kubernetes cluster

To be able to use Horizontal Pod Autoscaler for automatically scaling the number of Pods based on observed CPU/memory utilization. A metrics-server should be deployed first to collect metrics from Kubelets by running the command below:
```
kubectl apply -f kubernetes/api-application/metrics-server.yaml
```
Then, we deploy the API applicaton deployment and expose it via a NodePort service and use a HPA(Horizontal Pod Autoscaler) to do the autoscaling.
```
kubectl apply -f kubernetes/api-application/deployment.yaml
kubectl apply -f kubernetes/api-application/service.yaml
kubectl apply -f kubernetes/api-application/hpa.yaml
```

Run `kubectl get all` to get all the resources deployed in the default namespace. The result is as follow:
```
NAME                             READY   STATUS    RESTARTS   AGE
pod/guts-demo-65594fdfd8-69w8j   1/1     Running   0          13m
pod/guts-demo-65594fdfd8-dxpff   1/1     Running   0          13m

NAME                        TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
service/guts-demo-service   NodePort    10.233.32.84   <none>        5000:32231/TCP   35m
service/kubernetes          ClusterIP   10.233.0.1     <none>        443/TCP          24d

NAME                        READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/guts-demo   2/2     2            2           20m

NAME                                   DESIRED   CURRENT   READY   AGE
replicaset.apps/guts-demo-57fdbc8894   0         0         0       20m
replicaset.apps/guts-demo-65594fdfd8   2         2         2       13m

NAME                                                REFERENCE              TARGETS         MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/guts-demo-hpa   Deployment/guts-demo   <unknown>/75%   1         10        2          11m
```

Now the application is deployed in the Kubernetes cluster and we can try the API calls via POSTMAN.
```
GET /api/v1/sales/all HTTP/1.1
Host: 172.18.8.101:32231
Authorization: JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGl0eSI6MSwiaWF0IjoxNjI4MTk2NTEwLCJuYmYiOjE2MjgxOTY1MTAsImV4cCI6MTYyODE5NjgxMH0.d7cAtlWQ11Mxi3jD0DmlADmq22JpvPnCqJCIquzZaVk
Content-Type: application/json
```
## Monitoring via Prometheus
To monitoring the status of resource in the Kubernetes cluster, kube-state-metrics and Prometheus will be deployed into the cluster to collect metrics about the state of the objects in the cluster.
```
kubectl apply -f kubernetes/prometheus/kube-state-metrics/
kubectl apply -f kubernetes/prometheus
```

Now we can check the metrics of the cluster via `http://172.18.8.101:30052/new/targets`.