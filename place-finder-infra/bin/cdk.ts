#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { BaseStackProps } from "../lib/types";
import { EcrStack, AgentCoreStack } from "../lib/stacks";

const app = new cdk.App();

// Override image URI via context:
//   npx cdk deploy --all -c imageUri=<account>.dkr.ecr.<region>.amazonaws.com/placefinder-mcp:<tag>
const existingImageUri = app.node.tryGetContext("imageUri") as
  | string
  | undefined;

const deploymentProps: BaseStackProps = {
  appName: "placeFinder",
  // Uncomment to pin to a specific account/region:
  // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
};

// ECR repository — always created as infrastructure
const ecrStack = new EcrStack(app, "placeFinder-EcrStack", deploymentProps);

// Image URI: context override or default to ECR :latest
const imageUri = existingImageUri || `${ecrStack.repositoryUri}:latest`;

if (existingImageUri) {
  console.log(`Using provided image URI: ${existingImageUri}`);
} else {
  console.log(`Using default ECR image URI: ${imageUri}`);
}

// AgentCore stack — Runtime, Memory, Observability
const agentCoreStack = new AgentCoreStack(app, "placeFinder-AgentCoreStack", {
  ...deploymentProps,
  imageUri,
});

agentCoreStack.addDependency(ecrStack);
