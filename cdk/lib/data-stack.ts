import * as cdk from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as elasticache from "aws-cdk-lib/aws-elasticache";
import * as opensearchserverless from "aws-cdk-lib/aws-opensearchserverless";
import { Construct } from "constructs";

export interface DataStackProps extends cdk.StackProps {
  envName: string;
  vpc: ec2.IVpc;
  lambdaSecurityGroup: ec2.ISecurityGroup;
  aossVpcEndpointId: string;
}

export class DataStack extends cdk.Stack {
  public readonly aossEndpoint: string;
  public readonly aossCollectionArn: string;
  public readonly cardsTable: dynamodb.ITable;
  public readonly redisEndpoint: string;

  constructor(scope: Construct, id: string, props: DataStackProps) {
    super(scope, id, props);

    const collectionName = `rise-scout-${props.envName}`;

    // OpenSearch Serverless encryption policy
    const encryptionPolicy = new opensearchserverless.CfnSecurityPolicy(this, "AossEncryptionPolicy", {
      name: `${collectionName}-enc`,
      type: "encryption",
      policy: JSON.stringify({
        Rules: [
          {
            Resource: [`collection/${collectionName}`],
            ResourceType: "collection",
          },
        ],
        AWSOwnedKey: true,
      }),
    });

    // AOSS network policy
    const networkPolicy = new opensearchserverless.CfnSecurityPolicy(this, "AossNetworkPolicy", {
      name: `${collectionName}-net`,
      type: "network",
      policy: JSON.stringify([
        {
          Rules: [
            {
              Resource: [`collection/${collectionName}`],
              ResourceType: "collection",
            },
          ],
          AllowFromPublic: false,
          SourceVPCEs: [props.aossVpcEndpointId],
        },
      ]),
    });

    // AOSS collection
    const collection = new opensearchserverless.CfnCollection(
      this,
      "AossCollection",
      {
        name: collectionName,
        type: "SEARCH",
        description: "Rise Scout contacts and listings",
      }
    );
    collection.addDependency(encryptionPolicy);
    collection.addDependency(networkPolicy);

    this.aossEndpoint = collection.attrCollectionEndpoint;
    this.aossCollectionArn = collection.attrArn;

    // DynamoDB cards table
    this.cardsTable = new dynamodb.Table(this, "CardsTable", {
      tableName: `rise-scout-cards-${props.envName}`,
      partitionKey: { name: "agent_id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: "expires_at",
      removalPolicy:
        props.envName === "prod"
          ? cdk.RemovalPolicy.RETAIN
          : cdk.RemovalPolicy.DESTROY,
    });

    // ElastiCache Redis
    const redisSg = new ec2.SecurityGroup(this, "RedisSg", {
      vpc: props.vpc,
      description: "Security group for Rise Scout Redis",
    });

    redisSg.addIngressRule(
      props.lambdaSecurityGroup,
      ec2.Port.tcp(6379),
      "Allow Lambda access to Redis"
    );

    const privateSubnets = props.vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
    });

    const redisSubnetGroup = new elasticache.CfnSubnetGroup(
      this,
      "RedisSubnetGroup",
      {
        description: "Rise Scout Redis subnet group",
        subnetIds: privateSubnets.subnetIds,
      }
    );

    const redis = new elasticache.CfnCacheCluster(this, "RedisCluster", {
      engine: "redis",
      cacheNodeType:
        props.envName === "prod" ? "cache.r6g.large" : "cache.t3.micro",
      numCacheNodes: 1,
      vpcSecurityGroupIds: [redisSg.securityGroupId],
      cacheSubnetGroupName: redisSubnetGroup.ref,
    });

    this.redisEndpoint = redis.attrRedisEndpointAddress;
  }
}
