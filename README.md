# See everything in cloud with a simple CLI
This is my idea to have a single CLI to query multiple providers, instead of constantly switching between e.g. `awscli`, `kubectl`, some UIs and so on. Here are the features I'm aiming to achieve:

- A simple cli that can run in terminal
- Runs only locally without any extra dependencies
- Query basically any API that returns structured data, ability to extend tool easily
- Query many regions/contexts/namespaces at once
- See relations between resources
- Visualize it readably a graph
- No knowledge of schema, work with regexes, to make it as simple as possible

# My current solution
**I'd warmly welcome any ideas or suggestions 🙂**

My current approach is to define a graph as a list of vertices and list of edges visualized in a `tree`-like output:

![image](https://github.com/bondyra/overread/assets/9467341/285dcaa7-1ffa-4076-bde8-5129afd0116a)

Each **vertex** (prepended with `+`) is some resource type(s), which we can scope to some namespace/region/context/whatever, define some filters and some display options (see all attrs, see default attrs or list just IDs/names).

Each **edge** (prepended with `@`) allows you to see how resources are related, e.g. which subnet is in which VPC. Edges are purely optional - without them you just have a simple "list" CLI.

So as an example, to get AWS VPCs in profile `foo` and region `us-east-1` , you write:
```
ov get vpc -s foo/us-east-1
```
To get pods in context `bar` and namespace `dev`, you write:
```
ov get pod -s bar/dev
```

And for the "edges" - to get a list of VPCs and its associated subnets, you write:
```
ov get vpc + subnet @ a/b
```
So `+` means essentially "a vertex" and `@` means "an edge".

So the picture at the top of this chapter can be translated as: 
```
get VPCs (named `my_networks`) and its subnets (`my_subnets`) and some pods (`my_pods`) nested in subnets by checking if both contain (`-r` option) the word `demo`
```

# Nodes
You define a node either after `get` (and `--` if you use global opts), or with `+`.
The syntax for a "node" is:
```
module_name.resource_type_regex some_optional_alias [-s|--space SOME_REGEX] [-v|--verbose] [-q|--quiet] [-i|--id-filter SOME_REGEX] [-f|--content-filter SOME_REGEX]
```
- `module_name` is a string that is in the name of file that actually reads, e.g. `aws` for `overread_aws.py`. More about this - see #modules
- `resource_type_regex` - regex of things supported here: **What is supported**
- `some_optional_alias` - just a user friendly name, it is used to define edges, and defaults to letters of alphabet - `a`, `b`, ...
- `--space` - a generalization of AWS profile + region or kubernetes context + namespace, or anything else. It should be in a form `dimension1/dimension2/...` and can be a regex - see what dimensions are defined by individual modules
- `--verbose` whether to list all JSON content
- `--quiet` whether to list just resource IDs (what is ID depends obviously on a module and resource type, e.g. for `k8s` it's always `metadata.name`)
- `--id-filter` display only resources with IDs that match this regex
- `--content-filter` display only resources for which their content matches this regex (JSONs are `json.dump`ed)

# Edges
You define an edge at any place with `@` symbol.
The edge syntax is:
```
@ alias1/alias2 [-n | --negate] [-r | --regex SOME_REGEX]
```

By default, aliases are related when ID of one is in JSON of another one.

You can also define the regex, which will match it for one alias, and then search in the second one - this could be handy to search for similar content.

Finally, you can negate the condition (match when no IDs match or when regex doesn't match).

# Global opts
To not repeat something all the time, you could write the global opts before everything else:
```
ov get -v -s aws=profile1/region1,k8s=.*/some_ns -- get vpc + pod (...)
```
The options are generally the same things as you define for nodes, you just need to prepend the spaces with module name, and you can divide "global module's spaces" with comma - just like above.

# Modules
The tool contains "builtin" modules that you could try out - for AWS and Kubernetes.

New ones should be easy to write - prepare similar `overread_MODULENAME.py` file, put it to directory, set env var OVERREAD_MODULE_PATHS to this directory path, and use your new feature.

**! Note that the builtin modules here doesn't ship with API clients (`kubernetes-asyncio`, `aioboto3`), you'll need to install them separately.**

# What is supported
**AWS** - list of resources I currently added is here: https://github.com/bondyra/overread/blob/master/overread/builtin_modules/aws.json#L8

**Kubernetes** - list of resources I currently added is here: https://github.com/bondyra/overread/blob/master/overread/builtin_modules/k8s.json#L2

# How it works under the sheets
It:
- Processes your input, defining what calls exactly to make
- Makes a tonne of calls with `asyncio`
- Joins the big heap of JSONs it gets reasonably
- Prints the colored tree based on the results

# Roadmap
A lot to do. Things I want to do next are:
- **Figure out the best way and syntax to use this tool**
- Decide if this should be REPL or should still be one-time action tool. Or maybe just go with UI right away (I don't like UIs though)
- Local caching of responses (should be relatively easy to do)
- Pagination
- Full kubernetes and AWS support
- Help command
- Auto completion
- Prettier tree (or maybe something else?)
- And many, many more

# Lastly
Demo version is in **releases** - it should work on Ubuntu, probably also MacOS. You can also build it from source.

Any ideas/proposals where this project should / shouldn't go are always very welcome.
