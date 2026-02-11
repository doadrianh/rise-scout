import * as path from "path";
import * as cdk from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as iam from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";
import { LambdaLayersConstruct } from "./constructs/lambda-layers";
import { LambdaFunctionsConstruct } from "./constructs/lambda-functions";

export interface ComputeStackProps extends cdk.StackProps {
  envName: string;
  vpc: ec2.IVpc;
  lambdaSecurityGroup: ec2.ISecurityGroup;
  aossEndpoint: string;
  aossCollectionArn: string;
  cardsTable: dynamodb.ITable;
  redisEndpoint: string;
}

export class ComputeStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    super(scope, id, props);

    // Resolve project root (2 levels up from cdk/lib/)
    const projectRoot = path.resolve(__dirname, "..", "..");

    const commonEnv: Record<string, string> = {
      RISE_SCOUT_ENV: props.envName,
      RISE_SCOUT_AOSS_ENDPOINT: props.aossEndpoint,
      RISE_SCOUT_CARDS_TABLE: props.cardsTable.tableName,
      RISE_SCOUT_REDIS_URL: `redis://${props.redisEndpoint}:6379/0`,
      POWERTOOLS_SERVICE_NAME: "rise-scout",
      POWERTOOLS_LOG_LEVEL: props.envName === "dev" ? "DEBUG" : "INFO",
    };

    const privateSubnets = props.vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
    });

    const lambdaRole = new iam.Role(this, "LambdaRole", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AWSLambdaVPCAccessExecutionRole"
        ),
      ],
    });

    // AOSS data access
    lambdaRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["aoss:APIAccessAll"],
        resources: [props.aossCollectionArn],
      })
    );

    // Bedrock invoke
    lambdaRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["bedrock:InvokeModel"],
        resources: ["*"],
      })
    );

    // DynamoDB access
    props.cardsTable.grantReadWriteData(lambdaRole);

    // Common dependency layer
    const layers = new LambdaLayersConstruct(this, "Layers", {
      envName: props.envName,
      projectRoot,
    });

    // Lambda functions
    const functions = new LambdaFunctionsConstruct(this, "Functions", {
      envName: props.envName,
      projectRoot,
      commonLayer: layers.commonLayer,
      role: lambdaRole,
      vpc: props.vpc,
      vpcSubnets: privateSubnets,
      securityGroups: [props.lambdaSecurityGroup],
      environment: commonEnv,
    });

    // EventBridge: daily score decay at 2 AM UTC
    new events.Rule(this, "ScoreDecaySchedule", {
      schedule: events.Schedule.cron({ hour: "2", minute: "0" }),
      targets: [new targets.LambdaFunction(functions.scoreDecay)],
    });

    // EventBridge: card refresh every 15 minutes
    new events.Rule(this, "CardRefreshSchedule", {
      schedule: events.Schedule.rate(cdk.Duration.minutes(15)),
      targets: [new targets.LambdaFunction(functions.cardRefresh)],
    });
  }
}
