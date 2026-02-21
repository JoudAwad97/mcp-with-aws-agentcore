import * as cdk from "aws-cdk-lib/core";
import { Construct } from "constructs";
import * as bedrockagentcore from "aws-cdk-lib/aws-bedrockagentcore";
import * as iam from "aws-cdk-lib/aws-iam";
import { BaseStackProps } from "../types";

export interface GatewayStackProps extends BaseStackProps {
  /** AgentCore Runtime ID (from AgentCoreStack output) */
  runtimeId: string;
  /** AgentCore Runtime ARN (from AgentCoreStack output) */
  runtimeArn: string;
}

/**
 * AgentCore Gateway stack.
 *
 * Provisions:
 *  - AgentCore Gateway (MCP protocol, no authorization)
 *  - Gateway Target pointing to the MCP server Runtime
 *  - IAM role for the Gateway to invoke the Runtime
 *
 * WARNING: authorizerType "NONE" is for development/demo only.
 * For production, use CUSTOM_JWT or AWS_IAM.
 */
export class GatewayStack extends cdk.Stack {
  readonly gateway: bedrockagentcore.CfnGateway;
  readonly gatewayTarget: bedrockagentcore.CfnGatewayTarget;

  constructor(scope: Construct, id: string, props: GatewayStackProps) {
    super(scope, id, props);

    const region = cdk.Stack.of(this).region;
    const accountId = cdk.Stack.of(this).account;

    // =========================================================================
    // Gateway IAM Role
    // =========================================================================

    const gatewayRole = new iam.Role(this, "GatewayRole", {
      assumedBy: new iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
      description: `IAM role for ${props.appName} AgentCore Gateway`,
    });

    // Allow the Gateway to invoke the Runtime
    gatewayRole.addToPolicy(
      new iam.PolicyStatement({
        sid: "InvokeRuntime",
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock-agentcore:InvokeRuntime",
          "bedrock-agentcore:InvokeAgentRuntime",
        ],
        resources: [props.runtimeArn, `${props.runtimeArn}/*`],
      }),
    );

    // =========================================================================
    // AgentCore Gateway
    // =========================================================================

    this.gateway = new bedrockagentcore.CfnGateway(this, "Gateway", {
      name: `${props.appName}-Gateway`,
      protocolType: "MCP",
      roleArn: gatewayRole.roleArn,
      authorizerType: "NONE",
      description: `${props.appName} MCP Gateway — routes requests to the MCP server Runtime`,
    });

    // =========================================================================
    // Gateway Target — MCP Server (Runtime)
    // =========================================================================

    // Construct the Runtime MCP endpoint URL
    const runtimeEndpoint = `https://bedrock-agentcore-runtime.${region}.amazonaws.com/runtimes/${props.runtimeId}`;

    this.gatewayTarget = new bedrockagentcore.CfnGatewayTarget(
      this,
      "McpTarget",
      {
        name: `${props.appName}-McpTarget`,
        gatewayIdentifier: this.gateway.attrGatewayIdentifier,
        targetConfiguration: {
          mcp: {
            mcpServer: {
              endpoint: runtimeEndpoint,
            },
          },
        },
        // NoAuth: omit credentialProviderConfigurations entirely.
        // MCP server targets support NoAuth (no outbound credentials).
        // For production, use OAUTH with a registered credential provider.
        description: "MCP server target pointing to the AgentCore Runtime",
      },
    );

    // Ensure the target is created after the gateway
    this.gatewayTarget.addDependency(this.gateway);

    // =========================================================================
    // Stack Outputs
    // =========================================================================

    new cdk.CfnOutput(this, "GatewayId", {
      value: this.gateway.attrGatewayIdentifier,
      description: "AgentCore Gateway ID",
      exportName: `${props.appName}-GatewayId`,
    });

    new cdk.CfnOutput(this, "GatewayArn", {
      value: this.gateway.attrGatewayArn,
      description: "AgentCore Gateway ARN",
      exportName: `${props.appName}-GatewayArn`,
    });

    new cdk.CfnOutput(this, "GatewayUrl", {
      value: this.gateway.attrGatewayUrl,
      description:
        "AgentCore Gateway URL — MCP clients connect to this endpoint",
      exportName: `${props.appName}-GatewayUrl`,
    });

    new cdk.CfnOutput(this, "GatewayTargetId", {
      value: this.gatewayTarget.attrTargetId,
      description: "Gateway Target ID",
      exportName: `${props.appName}-GatewayTargetId`,
    });
  }
}
