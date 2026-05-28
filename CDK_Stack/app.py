#!/usr/bin/env python3
from aws_cdk import App
from kafka_stack import KafkaStack

app = App()


KafkaStack(
    app, "KafkaStack",
    description="Stack deploying Kafka Cluster with VPC, Subnet, EC2, and Secrets Manager"
)

app.synth()
