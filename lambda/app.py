import base64
import datetime
import json
import os
from cgi import FieldStorage
from io import BytesIO

import boto3

client_bedrock = boto3.client('bedrock-runtime')
client_s3 = boto3.client('s3')


def parse_into_field_storage(fp, ctype, clength):
    fs = FieldStorage(
        fp=fp,
        environ={'REQUEST_METHOD': 'POST'},
        headers={
            'content-type': ctype,
            'content-length': clength
        },
        keep_blank_values=True
    )
    form = {}
    files = {}
    for f in fs.list:
        if f.filename:
            files.setdefault(f.name, []).append(f)
        else:
            form.setdefault(f.name, []).append(f.value)
    return form, files


def lambda_handler(event, context):
    print("boto3 version", boto3.__version__)
    print("headers", event["headers"])

    body_file = BytesIO(base64.b64decode(event["body"]))
    content_type = event['headers'].get('Content-Type', '')
    content_length = body_file.getbuffer().nbytes

    form, files = parse_into_field_storage(
        body_file,
        content_type,
        content_length
    )

    prompt = form["prompt"][0]
    img_data = files["img"][0].file.read()

    s3_response = client_s3.put_object(
        Body=img_data,
        Bucket=os.getenv("S3Bucket"),
        Key='test_' + datetime.datetime.today().strftime('%Y-%m-%d/%H-%M-%S') + ".jpg"
    )
    print("s3_response", s3_response)

    img_str = base64.b64encode(img_data).decode("utf-8")

    print("prompt", prompt)
    print("img len", len(img_str))

    response_bedrock = client_bedrock.invoke_model(
        contentType='application/json', accept='application/json',
        modelId='stability.stable-diffusion-xl-v1',
        body=json.dumps(
            {
                "text_prompts": [
                    {
                        "text": prompt,
                        "weight": 1
                    }
                ],
                "cfg_scale": 10,
                "seed": 0,
                "steps": 50,
                "width": 512,
                "height": 512,
                "init_image": img_str
            }
        ))

    response_bedrock_byte = json.loads(response_bedrock['body'].read())
    response_bedrock_base64 = response_bedrock_byte['artifacts'][0]['base64']
    response_bedrock_finalimage = base64.b64decode(response_bedrock_base64)
    poster_name = 'posterName_' + datetime.datetime.today().strftime('%Y-%m-%d/%H-%M-%S') + ".jpg"
    client_s3.put_object(
        Bucket=os.getenv("S3Bucket"),
        Body=response_bedrock_finalimage,
        Key=poster_name)

    generate_presigned_url = client_s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': os.getenv("S3Bucket"),
            'Key': poster_name
        },
        ExpiresIn=3600)

    print("generate_presigned_url", generate_presigned_url)
    return {
        'statusCode': 200,
        'body': json.dumps({
            "url": generate_presigned_url
        })
    }
