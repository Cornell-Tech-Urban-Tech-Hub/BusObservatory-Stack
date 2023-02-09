from aws_cdk import (
    Stack,
    aws_s3 as s3,
)
from constructs import Construct
import json

# TODO: this should be simpler
# TODO: from my_constructs import BusObservatoryLake
from bus_observatory_stack.my_constructs.Lake import BusObservatoryLake
from bus_observatory_stack.my_constructs.Grabber import BusObservatoryGrabber
from bus_observatory_stack.my_constructs.API import BusObservatoryAPI

class BusObservatoryStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            bucket_name: str,
            **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)

        ###########################################################
        # LOAD CONFIG
        ###########################################################
        feeds = json.load(open("feeds.json"))

        ###########################################################
        # S3 BUCKET
        ###########################################################
        bucket = s3.Bucket.from_bucket_name(self, bucket_name, bucket_name)

        ###########################################################
        # SCHEDULED GRABBERS
        # create the lambda and configure scheduled event
        # for each feed
        ###########################################################
        grabber = BusObservatoryGrabber(
            self,
            "BusObservatoryGrabber",
            region="us-east-1", #FIXME: this shouldnt be hardcoded but above doesnt seem to work with 'self.region'
            bucket=bucket,
            feeds=feeds
        )

        ###########################################################
        # DATA LAKE
        # crawlers
        # crawl schedule
        # governed tables for each folder/feed
        ###########################################################
        # #TODO: lake
        # lake = BusObservatoryLake(self,
        # "BusObservatoryLake",
        # region=self.region,
        # bucket = bucket,
        # feeds=feeds
        # )

        ###########################################################
        # API
        # lambda handler
        # gateway
        # custom domain
        ###########################################################
        # #TODO: api
        # api = BusObservatoryAPI(
        #     self,
        #     "BusObservatoryAPI",
        #     region=self.region,
        #     bucket = bucket,
        #     feeds = feeds
        #     )