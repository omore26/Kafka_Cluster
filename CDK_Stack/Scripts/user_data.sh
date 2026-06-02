#!/bin/bash
# 1. Update the computer's software
yum update -y
# 2. Install Java (needed to run Kafka)
yum install -y java-17-amazon-corretto wget

cd /home/ec2-user

# 3. Download the Kafka software from the internet
wget https://downloads.apache.org/kafka/3.9.2/kafka_2.13-3.9.2.tgz
# 4. Unpack the software
tar -xzf kafka_2.13-3.9.2.tgz

cd kafka_2.13-3.9.2

# 5. Start Zookeeper (the coordinator) in the background
nohup bin/zookeeper-server-start.sh config/zookeeper.properties > zookeeper.log 2>&1 &
# wait for zookeeper to Start
sleep 10

# 6. Configure Kafka with private IP for internal network communication
PRIVATE_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)
echo "advertised.listeners=PLAINTEXT://$PRIVATE_IP:9092" >> config/server.properties

# 7. Start the Kafka server itself in the background
nohup bin/kafka-server-start.sh config/server.properties > kafka.log 2>&1 &

# Fetch Kafka secret securely from AWS Secrets Manager using dynamic secret name placeholder
SECRET_VALUE=$(aws secretsmanager get-secret-value \
  --secret-id DYNAMIC_SECRET_NAME \
  --region us-east-1 \
  --query SecretString \
  --output text)

# Extract Kafka username and password from the secret
KAFKA_USERNAME=$(echo $SECRET_VALUE | python3 -c "import sys, json; print(json.load(sys.stdin)['kafka_username'])")
KAFKA_PASSWORD=$(echo $SECRET_VALUE | python3 -c "import sys, json; print(json.load(sys.stdin)['kafka_password'])")

echo "Kafka username fetched from Secrets Manager"
