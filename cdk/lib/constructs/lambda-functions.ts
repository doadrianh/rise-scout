import { execSync } from "child_process";
import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";

const enum Fn {
  ContactConsumer,
  ListingConsumer,
  ScoreDecay,
  CardRefresh,
}

interface FunctionConfig {
  constructId: string;
  functionName: string;
  handlerDir: string;
  handler: string;
  timeout: cdk.Duration;
  memorySize: number;
}

export interface LambdaFunctionsProps {
  envName: string;
  projectRoot: string;
  commonLayer: lambda.ILayerVersion;
  role: iam.IRole;
  vpc: ec2.IVpc;
  vpcSubnets: ec2.SubnetSelection;
  securityGroups: ec2.ISecurityGroup[];
  environment: Record<string, string>;
}

export class LambdaFunctionsConstruct extends Construct {
  public readonly contactConsumer: lambda.Function;
  public readonly listingConsumer: lambda.Function;
  public readonly scoreDecay: lambda.Function;
  public readonly cardRefresh: lambda.Function;

  constructor(scope: Construct, id: string, props: LambdaFunctionsProps) {
    super(scope, id);

    const configs: Record<Fn, FunctionConfig> = {
      [Fn.ContactConsumer]: {
        constructId: "ContactConsumer",
        functionName: `rise-scout-contact-consumer-${props.envName}`,
        handlerDir: "contact_consumer",
        handler: "lambdas.contact_consumer.handler.handler",
        timeout: cdk.Duration.seconds(60),
        memorySize: 512,
      },
      [Fn.ListingConsumer]: {
        constructId: "ListingConsumer",
        functionName: `rise-scout-listing-consumer-${props.envName}`,
        handlerDir: "listing_consumer",
        handler: "lambdas.listing_consumer.handler.handler",
        timeout: cdk.Duration.seconds(60),
        memorySize: 512,
      },
      [Fn.ScoreDecay]: {
        constructId: "ScoreDecay",
        functionName: `rise-scout-score-decay-${props.envName}`,
        handlerDir: "score_decay",
        handler: "lambdas.score_decay.handler.handler",
        timeout: cdk.Duration.minutes(5),
        memorySize: 1024,
      },
      [Fn.CardRefresh]: {
        constructId: "CardRefresh",
        functionName: `rise-scout-card-refresh-${props.envName}`,
        handlerDir: "card_refresh",
        handler: "lambdas.card_refresh.handler.handler",
        timeout: cdk.Duration.minutes(5),
        memorySize: 1024,
      },
    };

    const createFunction = (config: FunctionConfig): lambda.Function => {
      const { projectRoot } = props;

      return new lambda.Function(this, config.constructId, {
        functionName: config.functionName,
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: config.handler,
        code: lambda.Code.fromAsset(projectRoot, {
          bundling: {
            image: lambda.Runtime.PYTHON_3_11.bundlingImage,
            local: {
              tryBundle(outputDir: string): boolean {
                try {
                  execSync(
                    `cp -r src/rise_scout "${outputDir}/rise_scout" && ` +
                      `mkdir -p "${outputDir}/lambdas/${config.handlerDir}" && ` +
                      `cp -r src/lambdas/${config.handlerDir}/* "${outputDir}/lambdas/${config.handlerDir}/"`,
                    { cwd: projectRoot }
                  );
                  return true;
                } catch {
                  return false;
                }
              },
            },
            command: [
              "bash",
              "-c",
              `cp -r /asset-input/src/rise_scout /asset-output/rise_scout && ` +
                `mkdir -p /asset-output/lambdas/${config.handlerDir} && ` +
                `cp -r /asset-input/src/lambdas/${config.handlerDir}/* /asset-output/lambdas/${config.handlerDir}/`,
            ],
          },
        }),
        layers: [props.commonLayer],
        role: props.role,
        vpc: props.vpc,
        vpcSubnets: props.vpcSubnets,
        securityGroups: props.securityGroups,
        environment: props.environment,
        timeout: config.timeout,
        memorySize: config.memorySize,
      });
    };

    this.contactConsumer = createFunction(configs[Fn.ContactConsumer]);
    this.listingConsumer = createFunction(configs[Fn.ListingConsumer]);
    this.scoreDecay = createFunction(configs[Fn.ScoreDecay]);
    this.cardRefresh = createFunction(configs[Fn.CardRefresh]);
  }
}
