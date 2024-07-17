# sam-boilerplate

## Build

````shell
sam build
````

## Deploy

### First time

````shell
sam deploy --guided --parameter-overrides Stage=staging
````

### Normal

````shell
sam deploy --config-env staging
````