#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { BaseStackProps } from "../lib/types";
import { EcrStack, AgentCoreStack, GatewayStack } from "../lib/stacks";

const app = new cdk.App();

// Override image URI via context:
//   npx cdk deploy --all -c imageUri=<account>.dkr.ecr.<region>.amazonaws.com/placefinder-mcp:<tag>
const existingImageUri = app.node.tryGetContext("imageUri") as
  | string
  | undefined;

const appName = "placeFinder";
const ecrRepoName = `${appName.toLowerCase()}-mcp`;

const deploymentProps: BaseStackProps = {
  appName,
  // Uncomment to pin to a specific account/region:
  // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
};

// ECR repository — always created as infrastructure
new EcrStack(app, `${appName}-EcrStack`, deploymentProps);

// Build default image URI from account/region tokens (no cross-stack reference)
const defaultImageUri = `${cdk.Aws.ACCOUNT_ID}.dkr.ecr.${cdk.Aws.REGION}.amazonaws.com/${ecrRepoName}:latest`;
const imageUri = existingImageUri || defaultImageUri;

if (existingImageUri) {
  console.log(`Using provided image URI: ${existingImageUri}`);
} else {
  console.log(`Using default ECR image URI: ${ecrRepoName}:latest`);
}

// AgentCore stack — Runtime, Memory, Observability
const agentCoreStack = new AgentCoreStack(app, `${appName}-AgentCoreStack`, {
  ...deploymentProps,
  imageUri,
});

// Gateway stack — MCP Gateway exposing the Runtime
new GatewayStack(app, `${appName}-GatewayStack`, {
  ...deploymentProps,
  runtimeId: agentCoreStack.runtime.agentRuntimeId,
  runtimeArn: agentCoreStack.runtime.agentRuntimeArn,
  cognitoUserPoolId: agentCoreStack.cognitoUserPoolId,
  cognitoClientId: agentCoreStack.cognitoClientId,
  cognitoTokenEndpoint: agentCoreStack.cognitoTokenEndpoint,
});
