# See everything in cloud with a simple CLI
This is my idea to have a single CLI to query multiple providers, instead of constantly switching between e.g. `awscli`, `kubectl`, some UIs and so on.

Here are the features I'm trying to achieve:

- A simple cli that can run in terminal
- Runs only locally without any extra dependencies
- Query basically any API that returns structured data, ability to extend tool easily
- Query many regions/contexts/namespaces at once
- See relations between resources
- Visualize it readably as a graph, tree or UI (?)
- No knowledge of schema, work with regexes, to make it as simple as possible

# The tool 
**Most importantly - I'd warmly welcome any ideas or suggestions!**

Some screenshot that shows what it can currently do: 
> get all VPCs ("`my_networks`"), its subnets ("`my_subnets`"), and k8s pods (`my_pods`) in subnets (matched if both contain the word `demo` somewhere):
![image](https://github.com/bondyra/overread/assets/9467341/285dcaa7-1ffa-4076-bde8-5129afd0116a)

## List the various resources

You can list anything by specifying resource type with (optional) module name
```
ov get aws/vpc

┕━ aws.vpc [a] (in default/eu-central-1)
   ┗━ vpc-abcdef123 (☑ root)
      └─CidrBlock: 172.31.0.0/16
```

You could also list completely separate resources if you need so:
```
ov get aws/vpc + k8s.pod

┢━ aws.vpc [a] (in default/eu-central-1)
┃  ┗━ vpc-abcdef123 (☑ root)
┃     └─CidrBlock: 172.31.0.0/16
┗━ k8s.pod [b] (in minikube/default)
   ┣━ test_abc (☑ root)
   ┗━ my-demo-pod (☑ root)
```
The item content you see above are some reasonable defaults.
You can control verbosity of list with `-q` and `-v` option, per "node"
```
ov get aws/vpc -v + aws/subnet -q

┢━ aws.vpc [a] (in default/eu-central-1)
┃  ┗━ vpc-abcdef123 (☑ root)
┃     ├─CidrBlock      : 172.31.0.0/16
┃     ├─DhcpOptionsId  : dopt-xxxx
┃     ├─State          : available
┃     ├─VpcId          : vpc-xxxx
┃     ├─OwnerId        : 1231232112
┃     ├─InstanceTenancy: default
┃     ├─CidrBlockAssociationSet
┃     │ └─┐
┃     │   ├─AssociationId: vpc-cidr-assoc-12321321
┃     │   ├─CidrBlock    : 172.31.0.0/16
┃     │   └─CidrBlockState
┃     │     └─State: associated
┃     └─IsDefault      : True
┗━ aws.subnet [b] (in default/eu-central-1)
   ┣━ subnet-a1234567 (☑ root)
   ┣━ subnet-b1234567 (☑ root)
   ┗━ subnet-c1234567 (☑ root)
```

You don't need to repeat the flags - "global opts" can be used:
```
ov get -q -- vpc + subnet

┢━ aws.vpc [a] (in default/eu-central-1)
┃  ┗━ vpc-abcdef123 (☑ root)
┗━ aws.subnet [b] (in default/eu-central-1)
   ┣━ subnet-a1234567 (☑ root)
   ┣━ subnet-b1234567 (☑ root)
   ┗━ subnet-c1234567 (☑ root)
```

Also, you can query with regexes:
```
ov get aws/vpc.*

┢━ aws/vpc [a] (in default/eu-central-1)
┃  ┗━ vpc-abcdef123 (☑ root)
┃     └─CidrBlock: 172.31.0.0/16
┗━ aws/vpc_peering [a] (in default/eu-central-1)
```

## List from multiple places at once

The tool allows you to query from multiple places at once with `-s` option:
```
ov get aws/vpc -s 'default/us-.*' -q

┢━ aws/vpc [a] (in default/us-east-2)
┃  ┗━ vpc-a1234567 (☑ root)
┣━ aws/vpc [a] (in default/us-east-1)
┃  ┗━ vpc-b1234567 (☑ root)
┣━ aws/vpc [a] (in default/us-west-1)
┃  ┗━ vpc-c1234567 (☑ root)
┗━ aws/vpc [a] (in default/us-west-2)
   ┗━ vpc-d1234567 (☑ root)
```

`-s` option means different things between "providers" - for AWS, it's `PROFILE/REGION`, but for k8s it's `CONTEXT/NAMESPACE`, e.g. "get all pods from all contexts in `kube-` namespaces":
```
ov get pod -s '.*/kube-.*' -q

┢━ k8s/pod [a] (in minikube/kube-node-lease)
┣━ k8s/pod [a] (in minikube/kube-public)
┗━ k8s/pod [a] (in minikube/kube-system)
   ┣━ coredns-5dd5756b68-lg8mn (☑ root)
   ┣━ etcd-minikube (☑ root)
   ┣━ kube-apiserver-minikube (☑ root)
   ┣━ kube-controller-manager-minikube (☑ root)
   ┣━ kube-proxy-njg7n (☑ root)
   ┣━ kube-scheduler-minikube (☑ root)
   ┗━ storage-provisioner (☑ root)
```

`-s` option works in global opts too, but you must specify it per module:
```
ov get -s aws=default/eu-west-1 k8s=minikube/kube-public -- vpc + pod

┢━ aws/vpc [a] (in default/eu-west-1)
┃  ┗━ vpc-abcdef1 (☑ root)
┃     └─CidrBlock: 172.31.0.0/16
┗━ k8s/pod [b] (in minikube/kube-public)
```


## Filter the list to something that interests you
Tool provides two filters - by id or by content (matching on dumped JSON).

To see results when subnet ID starts with `subnet-[LETTER]`:
```
ov get subnet -i 'subnet-[a-z].*'

┕━ aws/subnet [a] (in default/eu-central-1)
   ┣━ subnet-a1234567 (☑ root)
   ┃  ├─AvailabilityZone: eu-central-1b
   ┃  └─CidrBlock       : 172.31.32.0/20
   ┗━ subnet-b1234567 (☑ root)
      ├─AvailabilityZone: eu-central-1c
      └─CidrBlock       : 172.31.0.0/20
```

To see the results when a subnet in some US region has a CIDR starting with `172.31.48`:
```
ov get subnet -s 'default/us.*' -f '172.31.48.*'

┢━ aws/subnet [a] (in default/us-east-2)
┣━ aws/subnet [a] (in default/us-east-1)
┃  ┗━ subnet-a1234567 (☑ root)
┃     ├─AvailabilityZone: us-east-1e
┃     └─CidrBlock       : 172.31.48.0/20
┣━ aws/subnet [a] (in default/us-west-1)
┗━ aws/subnet [a] (in default/us-west-2)
   ┗━ subnet-b1234567 (☑ root)
      ├─AvailabilityZone: us-west-2d
      └─CidrBlock       : 172.31.48.0/20
```

## Nest resources by defining graph "edges"
To see what subnets belong to which VPCs in all US regions for profile default:
```
ov get -q -s 'aws=default/us.*' -- vpc + subnet @ a/b

┢━ aws/vpc [a] (in default/us-east-2)
┃  ┗━ vpc-aaaaaaa (☑ root)
┃     ┗━ aws/subnet [b] (in default/us-east-2, by id)
┃        ┣━ subnet-a1234567 (☑ vpc-aaaaaaa)
┃        ┣━ subnet-b1234567 (☑ vpc-aaaaaaa)
┃        ┗━ subnet-c1234567 (☑ vpc-aaaaaaa)
┣━ aws/vpc [a] (in default/us-east-1)
┃  ┗━ vpc-yyyyyyyy (☑ root)
┃     ┗━ aws/subnet [b] (in default/us-east-1, by id)
┃        ┣━ subnet-d1234567 (☑ vpc-yyyyyyyy)
┃        ┣━ subnet-e1234567 (☑ vpc-yyyyyyyy)
┃        ┣━ subnet-f1234567 (☑ vpc-yyyyyyyy)
┃        ┣━ subnet-g1234567 (☑ vpc-yyyyyyyy)
┃        ┣━ subnet-h1234567 (☑ vpc-yyyyyyyy)
┃        ┗━ subnet-i1234567 (☑ vpc-yyyyyyyy)
┣━ aws/vpc [a] (in default/us-west-1)
┃  ┗━ vpc-xxxxxxx (☑ root)
┃     ┗━ aws/subnet [b] (in default/us-west-1, by id)
┃        ┣━ subnet-j1234567 (☑ vpc-xxxxxxx)
┃        ┗━ subnet-k1234567 (☑ vpc-xxxxxxx)
┗━ aws/vpc [a] (in default/us-west-2)
   ┗━ vpc-zzzzzzzz (☑ root)
      ┗━ aws/subnet [b] (in default/us-west-2, by id)
         ┣━ subnet-l1234567 (☑ vpc-zzzzzzzz)
         ┗━ subnet-m1234567 (☑ vpc-zzzzzzzz)
```

You can also specify "alias" for "nodes", to get more comprehensible names:
```
ov get -q -- vpc networks + subnet subnets @ networks/subnets

┕━ aws/vpc [networks] (in default/eu-central-1)
   ┗━ vpc-aaaaaaa (☑ root)
      ┕━ aws/subnet [subnets] (in default/eu-central-1, by id)
         ┣━ subnet-a1234567 (☑ vpc-aaaaaaa)
         ┣━ subnet-b1234567 (☑ vpc-aaaaaaa)
         ┗━ subnet-c1234567 (☑ vpc-aaaaaaa)
```

You can also nest resources with a common text met in both contents:
```
ov get subnet my_subnets + pod my_pods -q @ my_subnets/my_pods -t 'demo'

┕━ aws/subnet [my_subnets] (in default/eu-central-1)
   ┣━ subnet-a1234567 (☑ root)
   ┃  ├─AvailabilityZone: eu-central-1b
   ┃  ├─CidrBlock       : 172.31.32.0/20
   ┃  ┕━ k8s/pod [my_pods] (in minikube/default, contains "demo") <no match>
   ┣━ subnet-b1234567 (☑ root)
   ┃  ├─AvailabilityZone: eu-central-1a
   ┃  ├─CidrBlock       : 172.31.16.0/20
   ┃  ┕━ k8s/pod [my_pods] (in minikube/default, contains "demo")
   ┃     ┗━ my-demo-pod (☑ demo)
   ┗━ subnet-c1234567 (☑ root)
      ├─AvailabilityZone: eu-central-1c
      ├─CidrBlock       : 172.31.0.0/20
      ┕━ k8s/pod [my_pods] (in minikube/default, contains "demo") <no match>
```

# Installation
```
pip install https://github.com/bondyra/overread/releases/download/v0.0.8/overread-0.0.8-py3-none-any.whl
```

# Modules
The tool contains "builtin" modules that you could try out - for AWS and Kubernetes.

New ones should be easy to write - prepare similar `overread_MODULENAME.py` file, put it to directory, set env var OVERREAD_MODULE_PATHS to this directory path, and use your new feature.

# What is supported
**AWS** - list of resources I currently added is here: https://github.com/bondyra/overread/blob/master/overread/builtin_modules/aws.json#L8

**Kubernetes** - list of resources I currently added is here: https://github.com/bondyra/overread/blob/master/overread/builtin_modules/k8s.json#L2

# How it works under the sheets
It:
- Processes your input, defining what calls exactly to make
- Makes a tonne of calls with `asyncio`
- Joins the big heap of JSONs it gets reasonably
- Prints the colored tree based on the results
- 
