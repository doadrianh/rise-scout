import * as fs from "fs";
import * as path from "path";
import { execSync } from "child_process";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";

export interface LambdaLayersProps {
  envName: string;
  projectRoot: string;
}

export class LambdaLayersConstruct extends Construct {
  public readonly commonLayer: lambda.LayerVersion;

  constructor(scope: Construct, id: string, props: LambdaLayersProps) {
    super(scope, id);

    const layersDir = path.join(
      props.projectRoot,
      "cdk",
      "layers",
      "common"
    );
    fs.mkdirSync(layersDir, { recursive: true });

    // Generate pinned requirements.txt from pyproject.toml (excludes project itself)
    const requirementsTxt = execSync(
      "uv pip compile pyproject.toml --no-header --color never",
      { cwd: props.projectRoot, encoding: "utf-8" }
    );
    fs.writeFileSync(path.join(layersDir, "requirements.txt"), requirementsTxt);

    this.commonLayer = new lambda.LayerVersion(this, "CommonDeps", {
      layerVersionName: `rise-scout-common-deps-${props.envName}`,
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
      code: lambda.Code.fromAsset(layersDir, {
        bundling: {
          image: lambda.Runtime.PYTHON_3_11.bundlingImage,
          command: [
            "bash",
            "-c",
            "pip install -r /asset-input/requirements.txt -t /asset-output/python",
          ],
        },
      }),
      description: "Common Python dependencies for Rise Scout lambdas",
    });
  }
}
