# Configuration parameters for Kafka AWS Infrastructure CDK Stack

REGION = "us-east-1"

PROJECT_NAME = "Kafka"
VPC_CIDR = "10.0.0.0/16"

INSTANCE_TYPE = "t3.micro"
INSTANCE_COUNT = 3

SSH_PORT = 22
KAFKA_PORT = 9092
ZOOKEEPER_PORT = 2181

KAFKA_SECRET_NAME = "Kafka-Credentials"

