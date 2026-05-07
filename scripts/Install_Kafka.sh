#!/bin/bash

# 1. Update the computer's existing software to the latest versions
yum update -y

# 2. Install Java (the engine Kafka needs to run) and a tool to download files (wget)
yum install -y java-17-amazon-corretto wget

# 3. Move into the home folder where we want to keep our files
cd /home/ec2-user

# 4. Download the Kafka software from the internet
wget https://downloads.apache.org/kafka/3.9.2/kafka_2.13-3.9.2.tgz

# 5. "Unzip" or unpack the software we just downloaded
tar -xzf kafka_2.13-3.9.2.tgz

# 6. Enter the newly created folder where the software lives
cd kafka_2.13-3.9.2

# 7. Start the "Coordinator" (Zookeeper) in the background so it stays running
nohup bin/zookeeper-server-start.sh config/zookeeper.properties > zookeeper.log 2>&1 &

# 8. Give the Coordinator a few seconds to wake up
sleep 10

# 9. Configure Kafka to be reachable from the internet (very important for testing!)
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "advertised.listeners=PLAINTEXT://$PUBLIC_IP:9092" >> config/server.properties

# 10. Start the "Data Server" (Kafka) itself in the background
nohup bin/kafka-server-start.sh config/server.properties > kafka.log 2>&1 &


