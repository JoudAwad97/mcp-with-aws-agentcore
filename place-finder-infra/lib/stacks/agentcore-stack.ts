import * as cdk from "aws-cdk-lib/core";
import { Construct } from "constructs";
import * as agentcore from "@aws-cdk/aws-bedrock-agentcore-alpha";
import * as iam from "aws-cdk-lib/aws-iam";
import * as logs from "aws-cdk-lib/aws-logs";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import { BaseStackProps } from "../types";

export interface AgentCoreStackProps extends BaseStackProps {
  /** Full ECR image URI (e.g. 123456789012.dkr.ecr.us-east-2.amazonaws.com/placefinder-mcp:latest) */
  imageUri: string;
}

/**
 * AgentCore infrastructure stack.
 *
 * Provisions:
 *  - Secrets Manager secret for the Google API key
 *  - AgentCore Runtime (container-based MCP server)
 *  - AgentCore Memory (user preference + semantic + summary strategies)
 *  - X-Ray / CloudWatch observability
 */
export class AgentCoreStack extends cdk.Stack {
  readonly runtime: agentcore.Runtime;
  readonly memory: agentcore.Memory;

  constructor(scope: Construct, id: string, props: AgentCoreStackProps) {
    super(scope, id, props);

    const region = cdk.Stack.of(this).region;
    const accountId = cdk.Stack.of(this).account;

    // =========================================================================
    // Secrets
    // =========================================================================

    // Google API key (Places + Weather) — update after deployment:
    //   aws secretsmanager put-secret-value --secret-id <appName>/google-api-key \
    //     --secret-string '{"api_key":"your-key"}'
    const googleApiSecret = new secretsmanager.Secret(this, "GoogleApiSecret", {
      secretName: `${props.appName}/google-api-key`,
      description:
        "Google API key for Places & Weather APIs. Update after deployment.",
      secretObjectValue: {
        api_key: cdk.SecretValue.unsafePlainText(""),
      },
    });

    // =========================================================================
    // AgentCore Memory
    // =========================================================================

    this.memory = new agentcore.Memory(this, "Memory", {
      memoryName: `${props.appName}_memory`,
      description: `${props.appName} long-term memory with user preference, semantic, and summary strategies`,
      memoryStrategies: [
        agentcore.MemoryStrategy.usingUserPreference({
          name: "user_preference_strategy",
          namespaces: ["/preferences/{actorId}/"],
        }),
        agentcore.MemoryStrategy.usingSemantic({
          name: "semantic_strategy",
          namespaces: ["/facts/{actorId}/"],
        }),
        agentcore.MemoryStrategy.usingSummarization({
          name: "summary_strategy",
          namespaces: ["/summaries/{sessionId}/"],
        }),
      ],
    });

    // =========================================================================
    // AgentCore Runtime
    // =========================================================================

    const artifact = agentcore.AgentRuntimeArtifact.fromImageUri(
      props.imageUri,
    );

    this.runtime = new agentcore.Runtime(this, "Runtime", {
      runtimeName: `${props.appName}_mcp`,
      agentRuntimeArtifact: artifact,
      description: `${props.appName} MCP server (Places, Weather, User Preferences)`,
      protocolConfiguration: agentcore.ProtocolType.HTTP,
      networkConfiguration:
        agentcore.RuntimeNetworkConfiguration.usingPublicNetwork(),
      environmentVariables: {
        // AWS
        AWS_REGION: region,

        // AgentCore resources
        AGENTCORE_MEMORY_ID: this.memory.memoryId,

        // Google API key is fetched by the app via Secrets Manager
        GOOGLE_API_SECRET_NAME: googleApiSecret.secretName,

        // OpenTelemetry observability
        AGENT_OBSERVABILITY_ENABLED: "true",
        OTEL_SERVICE_NAME: `${props.appName}-mcp`,
        OTEL_PYTHON_DISTRO: "aws_distro",
        OTEL_PYTHON_CONFIGURATOR: "aws_configurator",
        OTEL_EXPORTER_OTLP_PROTOCOL: "http/protobuf",
        OTEL_TRACES_EXPORTER: "otlp",
        OTEL_METRICS_EXPORTER: "otlp",
        OTEL_LOGS_EXPORTER: "otlp",
        OTEL_EXPORTER_OTLP_ENDPOINT: `https://xray.${region}.amazonaws.com`,
        OTEL_PROPAGATORS: "xray,tracecontext,baggage",
        OTEL_RESOURCE_ATTRIBUTES: [
          `service.name=${props.appName}-mcp`,
          `aws.log.group.names=/aws/bedrock-agentcore/runtimes/${props.appName}-mcp`,
          `cloud.region=${region}`,
        ].join(","),
        OTEL_EXPORTER_OTLP_LOGS_HEADERS: [
          `x-aws-log-group=/aws/bedrock-agentcore/runtimes/${props.appName}-mcp`,
          "x-aws-log-stream=runtime-logs",
          "x-aws-metric-namespace=bedrock-agentcore",
        ].join(","),
      },
    });

    // -------------------------------------------------------------------------
    // Additional IAM permissions for the runtime execution role
    // -------------------------------------------------------------------------

    // ECR — pull container image
    this.runtime.addToRolePolicy(
      new iam.PolicyStatement({
        sid: "ECRPullImage",
        effect: iam.Effect.ALLOW,
        actions: [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ],
        resources: [
          `arn:aws:ecr:${region}:${accountId}:repository/${props.appName.toLowerCase()}-*`,
        ],
      }),
    );
    this.runtime.addToRolePolicy(
      new iam.PolicyStatement({
        sid: "ECRAuth",
        effect: iam.Effect.ALLOW,
        actions: ["ecr:GetAuthorizationToken"],
        resources: ["*"],
      }),
    );

    // Secrets Manager — read Google API key at runtime
    googleApiSecret.grantRead(this.runtime);

    // AgentCore Memory — full access to memory resources
    this.runtime.addToRolePolicy(
      new iam.PolicyStatement({
        sid: "AgentCoreMemoryAccess",
        effect: iam.Effect.ALLOW,
        actions: ["bedrock-agentcore:*"],
        resources: [
          `arn:aws:bedrock-agentcore:${region}:${accountId}:memory/*`,
        ],
      }),
    );

    // S3 Vector Store — used by memory for semantic search
    this.runtime.addToRolePolicy(
      new iam.PolicyStatement({
        sid: "S3VectorStoreAccess",
        effect: iam.Effect.ALLOW,
        actions: [
          "s3vectors:QueryVectors",
          "s3vectors:PutVectors",
          "s3vectors:GetVectors",
          "s3vectors:DeleteVectors",
        ],
        resources: [`arn:aws:s3vectors:${region}:${accountId}:bucket/*`],
      }),
    );

    // CloudWatch Logs delivery (OTLP)
    this.runtime.addToRolePolicy(
      new iam.PolicyStatement({
        sid: "OTLPCloudWatchExport",
        effect: iam.Effect.ALLOW,
        actions: [
          "logs:PutLogEvents",
          "logs:CreateLogStream",
          "logs:CreateLogGroup",
          "logs:DescribeLogStreams",
        ],
        resources: [
          `arn:aws:logs:${region}:${accountId}:log-group:/aws/vendedlogs/bedrock-agentcore/*`,
          `arn:aws:logs:${region}:${accountId}:log-group:/aws/vendedlogs/bedrock-agentcore/*:log-stream:*`,
          `arn:aws:logs:${region}:${accountId}:log-group:aws/spans:*`,
        ],
      }),
    );

    // CloudWatch Logs delivery API
    this.runtime.addToRolePolicy(
      new iam.PolicyStatement({
        sid: "CloudWatchLogsDelivery",
        effect: iam.Effect.ALLOW,
        actions: [
          "logs:PutDeliverySource",
          "logs:PutDeliveryDestination",
          "logs:CreateDelivery",
          "logs:GetDeliverySource",
          "logs:GetDeliveryDestination",
          "logs:GetDelivery",
          "logs:DeleteDeliverySource",
          "logs:DeleteDeliveryDestination",
          "logs:DeleteDelivery",
        ],
        resources: ["*"],
      }),
    );

    // =========================================================================
    // Observability — X-Ray → CloudWatch Logs resource policy
    // =========================================================================

    new logs.CfnResourcePolicy(this, "XRayResourcePolicy", {
      policyName: `${props.appName}-XRayCloudWatchLogsAccess`,
      policyDocument: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
          {
            Effect: "Allow",
            Principal: { Service: "xray.amazonaws.com" },
            Action: ["logs:PutLogEvents", "logs:CreateLogStream"],
            Resource: `arn:aws:logs:${region}:${accountId}:log-group:aws/spans:*`,
          },
        ],
      }),
    });

    // =========================================================================
    // Stack Outputs
    // =========================================================================

    new cdk.CfnOutput(this, "RuntimeId", {
      value: this.runtime.agentRuntimeId,
      description: "AgentCore Runtime ID",
      exportName: `${props.appName}-RuntimeId`,
    });

    new cdk.CfnOutput(this, "RuntimeArn", {
      value: this.runtime.agentRuntimeArn,
      description: "AgentCore Runtime ARN",
      exportName: `${props.appName}-RuntimeArn`,
    });

    new cdk.CfnOutput(this, "MemoryId", {
      value: this.memory.memoryId,
      description: "AgentCore Memory ID",
      exportName: `${props.appName}-MemoryId`,
    });

    new cdk.CfnOutput(this, "MemoryArn", {
      value: this.memory.memoryArn,
      description: "AgentCore Memory ARN",
      exportName: `${props.appName}-MemoryArn`,
    });

    new cdk.CfnOutput(this, "GoogleApiSecretArn", {
      value: googleApiSecret.secretArn,
      description: "Google API key secret ARN",
      exportName: `${props.appName}-GoogleApiSecretArn`,
    });
  }
}
