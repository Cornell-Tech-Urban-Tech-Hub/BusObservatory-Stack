import os, json
import datetime as dt
import boto3
import io
import glob
import pandas as pd
import boto3

# https://stackoverflow.com/questions/45043554/how-to-read-a-list-of-parquet-files-from-s3-as-a-pandas-dataframe-using-pyarrow

# Read single parquet file from S3
def pd_read_s3_parquet(key, bucket, s3_client=None, **args):
    if s3_client is None:
        s3_client = boto3.client('s3')
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    return pd.read_parquet(io.BytesIO(obj['Body'].read()), **args)

# Read multiple parquets from a folder on S3 generated by spark
def pd_read_s3_multiple_parquets(
        filepath, 
        bucket, 
        s3=None, 
        s3_client=None, 
        verbose=False,
        **args
        ):
    # if not filepath.endswith('/'):
    #     filepath = filepath + '/'  # Add '/' to the end
    if s3_client is None:
        session = boto3.Session()
        s3_client = session.client('s3')
    if s3 is None:
        s3 = boto3.resource('s3')
    
    s3_keys = [item.key for item in s3.Bucket(bucket).objects.filter(Prefix=filepath)
            if item.key.endswith('.parquet')]
    if not s3_keys:
        print('No parquet found in', bucket, filepath)
    elif verbose:
        print('Load parquets:')
        for p in s3_keys: 
            print(p)
    dfs = [pd_read_s3_parquet(key, bucket=bucket, s3_client=s3_client, **args) 
        for key in s3_keys]
    return s3_keys, pd.concat(dfs, ignore_index=True)

def by_chunk(items, chunk_size=500):
    bucket = []
    for item in items:
        if len(bucket) >= chunk_size:
            yield bucket
            bucket = []
        bucket.append(item)
    yield bucket

def handler(event, context):

    # get config from the passed event
    region = event["region"]
    bucket_name = event["bucket_name"]
    system_id = event["system_id"]
    feed_config = event["feed_config"]
    prefix=f"feeds/{system_id}/INCOMING_"

    # read and concat all files into a single dataframe
    s3_keys, combined_df = pd_read_s3_multiple_parquets(prefix, bucket_name)

    # dump that dataframe back to compacted lake S3 as parquet
    current_time = dt.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H:%M:%S")
    s3_url = f"s3://{bucket_name}/feeds/{system_id}/COMPACTED_{system_id}_{formatted_time}.parquet"
    combined_df.to_parquet(
        s3_url, 
        compression="snappy",
        times="int96"
        )

    # delete all read files in file list
    #BUG: this fails for more than 999 objects "[ERROR] ClientError: An error occurred (MalformedXML) when calling the DeleteObjects operation: The XML you provided was not well-formed or did not validate against our published schema"

    # old solution
    # s3_client = boto3.client('s3')
    # response = s3_client.delete_objects(
    #     Bucket=bucket_name,
    #     Delete={
    #         'Objects': [{'Key': key} for key in s3_keys]
    #     }
    # )

    # new solution https://github.com/boto/boto3/issues/3447
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket(bucket_name)
    for items in by_chunk(s3_keys, 500): #TODO can go up to 1000?
        bucket.delete_objects(Delete={'Objects': [{'Key': key} for key in items]})


    # report summary
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"{system_id}: wrote {len(combined_df)} buses from {len(s3_keys)} files for {system_id} to {s3_url}",
        }),
    }


###############################################################################
# MAIN
# We only need this for local debugging.
###############################################################################

if __name__ == "__main__":
    context = None
    event = json.load(open("test_event.json"))
    handler(event, context)


