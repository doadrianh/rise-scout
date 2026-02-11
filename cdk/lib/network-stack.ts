import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";

export interface NetworkStackProps extends cdk.StackProps {
  envName: string;
}

export class NetworkStack extends cdk.Stack {
  public readonly vpc: ec2.IVpc;
  public readonly lambdaSecurityGroup: ec2.ISecurityGroup;
  public readonly aossVpcEndpointId: string;

  constructor(scope: Construct, id: string, props: NetworkStackProps) {
    super(scope, id, props);

    this.vpc = new ec2.Vpc(this, "Vpc", {
      maxAzs: 2,
      natGateways: props.envName === "prod" ? 2 : 1,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: "Private",
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
        {
          cidrMask: 28,
          name: "Public",
          subnetType: ec2.SubnetType.PUBLIC,
        },
      ],
    });

    this.lambdaSecurityGroup = new ec2.SecurityGroup(this, "LambdaSg", {
      vpc: this.vpc,
      description: "Security group for Rise Scout Lambda functions",
      allowAllOutbound: true,
    });

    // VPC Endpoints
    const aossEndpoint = this.vpc.addInterfaceEndpoint("AossEndpoint", {
      service: new ec2.InterfaceVpcEndpointAwsService("aoss"),
      securityGroups: [this.lambdaSecurityGroup],
    });
    this.aossVpcEndpointId = aossEndpoint.vpcEndpointId;

    this.vpc.addInterfaceEndpoint("BedrockEndpoint", {
      service: ec2.InterfaceVpcEndpointAwsService.BEDROCK_RUNTIME,
      securityGroups: [this.lambdaSecurityGroup],
    });

    this.vpc.addInterfaceEndpoint("StsEndpoint", {
      service: ec2.InterfaceVpcEndpointAwsService.STS,
      securityGroups: [this.lambdaSecurityGroup],
    });

    this.vpc.addGatewayEndpoint("DynamoEndpoint", {
      service: ec2.GatewayVpcEndpointAwsService.DYNAMODB,
    });
  }
}
