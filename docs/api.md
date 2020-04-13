
# API

- - - -
## POST ...

- - - -
## GET alive?
Tests if the service is alive.  
Used as a [Kubernetes](https://kubernetes.io/) liveness probe.  
- parameters
  * none
- result [(JSON-out)](#json-out)
  * **true**
- example
  ```bash     
  $ curl --silent -X GET http://${IP_ADDRESS}:${PORT}/alive?

  {"alive?":true}
  ```

- - - -
## GET ready?
Tests if the service is ready to handle requests.  
Used as a [Kubernetes](https://kubernetes.io/) readiness probe.
- parameters
  * none
- result [(JSON-out)](#json-out)
  * **true** when the service is ready
  * **false** when the service is not ready
- example
  ```bash     
  $ curl --silent -X GET http://${IP_ADDRESS}:${PORT}/ready?

  {"ready?":false}
  ```

- - - -
## GET sha
The git commit sha used to create the Docker image.
- parameters
  * none
- result [(JSON-out)](#json-out)
  * the 40 character commit sha string.
- example
  ```bash     
  $ curl --silent -X GET http://${IP_ADDRESS}:${PORT}/sha

  {"sha":"41d7e6068ab75716e4c7b9262a3a44323b4d1448"}
  ```


- - - -
## JSON in
- All methods pass their argument in a json hash in the http request body.
  * For `alive?`,`ready?` and `sha` you can use `''` (which is the default for `curl --data`) instead of `'{}'`.

- - - -
## JSON out      
- All methods return a json hash in the http response body.
  * If the method does not raise, a string key equals the method's name. eg
    ```bash
    $ curl --silent -X GET http://${IP_ADDRESS}:${PORT}/ready?

    {"ready?":true}
    ```
  * If the method raises an exception, a string key equals `"exception"`, with
    a json-hash as its value. eg
    ```bash
    $ curl --data 'not-json-hash' --silent -X GET http://${IP_ADDRESS}:${PORT}/ready? | jq      

    {
      "exception": {
        "path": "/ready",
        "body": "not-json-hash",
        "class": "SaverService",
        "message": "...",
        "backtrace": [
          ...
          "/usr/bin/rackup:23:in `<main>'"
        ]
      }
    }
    ```
