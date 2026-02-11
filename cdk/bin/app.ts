#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { NetworkStack } from "../lib/network-stack";
import { DataStack } from "../lib/data-stack";
import { ComputeStack } from "../lib/compute-stack";

const app = new cdk.App();
const env = app.node.tryGetContext("env") || "dev";

const networkStack = new NetworkStack(app, `RiseScout-${env}-Network`, {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || "us-west-2",
  },
  envName: env,
});

const dataStack = new DataStack(app, `RiseScout-${env}-Data`, {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || "us-west-2",
  },
  envName: env,
  vpc: networkStack.vpc,
  lambdaSecurityGroup: networkStack.lambdaSecurityGroup,
  aossVpcEndpointId: networkStack.aossVpcEndpointId,
});

new ComputeStack(app, `RiseScout-${env}-Compute`, {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || "us-west-2",
  },
  envName: env,
  vpc: networkStack.vpc,
  lambdaSecurityGroup: networkStack.lambdaSecurityGroup,
  aossEndpoint: dataStack.aossEndpoint,
  aossCollectionArn: dataStack.aossCollectionArn,
  cardsTable: dataStack.cardsTable,
  redisEndpoint: dataStack.redisEndpoint,
});
