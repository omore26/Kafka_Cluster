#!/usr/bin/env python3
import aws_cdk as cdk
import config
from Stacks.kafka_stack import KafkaStack

app = cdk.App()


KafkaStack(
    app, "KafkaStack",
    env = cdk.Environment(region=config.REGION),
    description="Stack deploying Kafka Cluster with VPC, Subnet, EC2, and Secrets Manager"
)

app.synth()
