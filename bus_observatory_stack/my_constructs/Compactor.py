from constructs import Construct

from aws_cdk import (
    Duration,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_alpha
)


class BusObservatoryCompactor(Construct):
    def __init__(
            self,
            scope: Construct, 
            id: str, 
            stack_config: dict,
            region: str, 
            bucket,
            **kwargs):

        super().__init__(scope, id, **kwargs)


        feeds=stack_config['feeds'] 
        # CREATE THE COMPACTOR LAMBDA
        # this will build and package an env using entry folder requirements.txt without need for layers

        handler = _lambda_alpha.PythonFunction(
            self,
            "BusObservatoryStack_Compactor_Lambda",
            entry="bus_observatory_stack/my_lambdas/lambda_Compactor",
            runtime=_lambda.Runtime.PYTHON_3_8,
            index="app.py",
            handler="handler",
            timeout=Duration.seconds(600), 
            memory_size=8192
        )

        
        #grant write access to handler on source bucket
        bucket.grant_read_write(handler.role)

        # CONFIGURE SCHEDULED EVENTS

        for system_id, feed_config in feeds.items():

            event_input = {
                "region": region,
                "bucket_name" : bucket.bucket_name,
                "system_id" : system_id,
                "feed_config" : feed_config
            }

            # create a named rule for each feed, runs every 1 minute
            events.Rule(
                self, 
                f"BusObservatory_Compactor_Rule_{system_id}",
                schedule=events.Schedule.rate(Duration.hours(24)),
                    targets = [
                        targets.LambdaFunction(
                            handler,
                            event=events.RuleTargetInput.from_object(event_input)
                            )
                        ],
                    description=f"BusObservatoryStack Compactor Rule for {system_id}"
                )
