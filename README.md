[![Github Action (main)](https://github.com/cyber-dojo/repler/actions/workflows/main.yml/badge.svg)](https://github.com/cyber-dojo/repler/actions)

- The source for the [cyberdojo/repler](https://hub.docker.com/r/cyberdojo/repler/tags) Docker image.
- A docker-containerized http micro-service for [cyber-dojo](http://cyber-dojo.org).

This repo currently has set 
`desired_count             = 0`
in the file deployment/terraform/deployment.tf

This is because the repler service is not starting properly, and so fails its health checks. Because
`ecs_wait_for_steady_state = true`
is set in the same file, it stalls in the CI pipeline, and no longer even attempts to deploy.

The error message from the logs on aws-prod are:
```
Sanic app name ‘cyber-dojo-repler’ not found.
App instantiation must occur outside if __name__ == ‘__main__’ block or by using an AppLoader.
```
Interestingly, these error messages do not appear on aws-beta.

- - - -
* ...
* [GET ready?](docs/api.md#get-ready)
* [GET alive?](docs/api.md#get-alive)  
* [GET sha](docs/api.md#get-sha)

- - - -
![cyber-dojo.org home page](https://github.com/cyber-dojo/cyber-dojo/blob/master/shared/home_page_snapshot.png)
