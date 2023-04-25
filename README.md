
###### Febuary 2023
# BusObservatory-Stack 

logs for the grabber are at `aws logs tail --follow /aws/lambda/BusObservatory-busobserva-BusObservatoryGrabberBus-4yD6z8VmsMAM`

# TO-DOs

## high priority

1. debug comapction solution (this branch)
    - add way to detect when compaction fails (more than n files with INCOMING prefix?)
    - how to fix it? throw an alarm? move them all to a dead letter queue?
2. remove all secrets so i can publish the code
3. Athena results bucket setup needs fixxing
    - right now the API is using a pre-existing athena bucket to temp hold the results of queries before `pythena` cleans them up (`arn:aws:s3:::aws-athena-query-results-870747888580-us-east-1`)
        - this is hardcoded in `my_lambdas/lambda_API/helpers.py`
    - to fix:
        - create a bucket in `my_constructs/API.py` using a dynamic name like `f"{bucket_name}-results"`
        - create a new Athena workgroup, setting the default query results for that workgroup to the
            - see https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_athena/CfnWorkGroup.html
        - make sure the crawler and lakeformation and the rest use this workgroup
        - grant the `my_handler` lambda `s3:*` on the resource `f"arn:aws:s3:::{bucket_name}-results"` and `f"arn:aws:s3:::{bucket_name}-results/*"`
        - in `my_lambdas/lambda_API/helpers.py` queries will automatically use this

## middle priority

1. API render feed pages daily and serve static (rather than gen from a query)
2. static image not working in API https://beta.busobservatory.org


## low priority

1. secure API
    - see https://pypi.org/project/aws-cdk-secure-api/#
    - see https://www.freecodecamp.org/news/how-to-add-jwt-authentication-in-fastapi/
    - or webauthn?
2. speed up large queries by migrating to boto3 vs pythena (https://medium.com/codex/connecting-to-aws-athena-databases-using-python-4a9194427638)
3. implement tests https://docs.aws.amazon.com/cdk/v2/guide/testing.html


## Description
This is a prototype fully-managed stack to replace the existing collection of SAM lambdas and independently managed reosurces (S3, EventBridge rules, Route53 records, Glue crawlers and databases etc.)

There are 3 main design goals:
1. to simplify and unify adminstration of the entire infrastructure
2. to implememt Lake Formation governed tables to automatically compact data lakes
3. to standardize on collection of UTM timestamps, with localization in the API
4. simplify addition of new feeds (ideally, be able to implement a simple web-based editor?)

The goal is to complete in Spring 2023 and migrate the existing data lakes over the summer.

## How to test lambdas LOCALLY
- more info here https://stackoverflow.com/questions/64689865/debugging-lambda-locally-using-cdk-not-sam
- embed a static test event and just pass it
- GENERALLY THIS IS A PITA

## how to view REMOTE logs for lambdas

1. get list of log groups `awslogs groups`
2. find the one that corresponds to the Stack ARN (output of `cdk deploy`)
3. tail and follow the log group `aws logs tail --follow {group}`


# How Configuration is handled

## At deployment
- `bus_observatory_stack/config/feeds.json` is loaded from the local disk
- Lambda grabber events are configured using this data
- the same feed config data is stored in an SSM Parameter with the format `/bucket-name/feeds/system-id` e.g. `/busobservatory-2/feeds/nyct_mta_bus_siri`

### For the Grabber
- the config for each feed is hard-coded in its lambda event at deployment

### For the API
- the config is read from the parameter store on each invocation
