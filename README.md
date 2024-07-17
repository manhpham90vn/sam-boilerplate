# sam-boilerplate

## Deploy

### First time

````shell
sam build
sam deploy --guided --parameter-overrides Stage=staging
````

### Normal

````shell
sam build
sam deploy --config-env staging --force-upload
````