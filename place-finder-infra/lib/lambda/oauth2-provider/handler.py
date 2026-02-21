"""
Custom Resource handler: creates/deletes an AgentCore OAuth2 credential provider.

Used by CDK to register Cognito credentials with AgentCore's token vault so
the Gateway can authenticate to the Runtime using OAuth.
"""

import json
import logging
import urllib.request

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def send_cfn_response(event, context, status, data=None, reason=""):
    physical_id = (
        (data or {}).get("credentialProviderArn")
        or event.get("PhysicalResourceId")
        or context.log_stream_name
    )
    body = json.dumps({
        "Status": status,
        "Reason": reason or f"See CloudWatch Log Stream: {context.log_stream_name}",
        "PhysicalResourceId": physical_id,
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "Data": data or {},
    }).encode("utf-8")

    req = urllib.request.Request(
        event["ResponseURL"], data=body, method="PUT",
        headers={"Content-Type": ""},
    )
    urllib.request.urlopen(req)


def lambda_handler(event, context):
    logger.info("Event: %s", json.dumps(event, default=str))
    props = event["ResourceProperties"]
    request_type = event["RequestType"]

    try:
        region = props["Region"]
        cognito_client = boto3.client("cognito-idp", region_name=region)
        control_client = boto3.client("bedrock-agentcore-control", region_name=region)

        if request_type in ("Create", "Update"):
            # On Update, try to delete the old provider first
            if request_type == "Update":
                try:
                    control_client.delete_oauth2_credential_provider(
                        name=props["ProviderName"],
                    )
                except Exception:
                    logger.warning("Could not delete old provider during update")

            # Look up the Cognito client secret
            desc = cognito_client.describe_user_pool_client(
                UserPoolId=props["UserPoolId"],
                ClientId=props["ClientId"],
            )
            client_secret = desc["UserPoolClient"]["ClientSecret"]

            discovery_url = (
                f"https://cognito-idp.{region}.amazonaws.com/"
                f"{props['UserPoolId']}/.well-known/openid-configuration"
            )

            resp = control_client.create_oauth2_credential_provider(
                name=props["ProviderName"],
                credentialProviderVendor="CustomOauth2",
                oauth2ProviderConfigInput={
                    "customOauth2ProviderConfig": {
                        "oauthDiscovery": {
                            "discoveryUrl": discovery_url,
                        },
                        "clientId": props["ClientId"],
                        "clientSecret": client_secret,
                    }
                },
            )
            provider_arn = resp["credentialProviderArn"]
            logger.info("Created OAuth2 provider: %s", provider_arn)

            send_cfn_response(event, context, "SUCCESS", {
                "credentialProviderArn": provider_arn,
            })

        elif request_type == "Delete":
            try:
                control_client.delete_oauth2_credential_provider(
                    name=props["ProviderName"],
                )
                logger.info("Deleted OAuth2 provider: %s", props["ProviderName"])
            except Exception:
                logger.warning("Could not delete provider (may not exist)")

            send_cfn_response(event, context, "SUCCESS")

    except Exception as e:
        logger.exception("Custom resource handler failed")
        send_cfn_response(event, context, "FAILED", reason=str(e))
