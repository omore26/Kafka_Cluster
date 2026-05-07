import boto3
import time


# This class acts as a blueprint to build our Kafka setup on AWS from scratch
class KafkaAWSInfra:
    def __init__(self, region="us-east-1"):
        # We start by picking which AWS "location" (region) we want to build in
        self.ec2 = boto3.resource("ec2", region_name=region)
        self.client = boto3.client("ec2", region_name=region)

        # These are placeholders where we'll store the IDs of the parts we build
        self.vpc = None
        self.internet_gateway = None
        self.subnet = None
        self.route_table = None
        self.security_group = None
        self.instances = []

    # ---------------- VPC ----------------
    # This creates a private space for our project to live in
    def create_vpc(self, cidr="10.0.0.0/16", name="Kafka-VPC-1"):
        self.vpc = self.ec2.create_vpc(CidrBlock=cidr)
        self.vpc.wait_until_available() 

        # Enable features so our computers can have easy-to-read names instead of just numbers
        self.vpc.modify_attribute(EnableDnsSupport={'Value': True})
        self.vpc.modify_attribute(EnableDnsHostnames={'Value': True})

        self.vpc.create_tags(Tags=[{"Key": "Name", "Value": name}])

        print("VPC created:", self.vpc.id)
        return self.vpc

    # ---------------- Internet Gateway ----------------
    # This builds a "front door" for our private space so it can connect to the internet
    def create_internet_gateway(self, name="Kafka-IGW-1"):
        self.internet_gateway = self.ec2.create_internet_gateway()
        self.internet_gateway.create_tags(
            Tags = [
                {
                    "Key":"Name",
                    "Value":name
                }
            ]
        )
        # Attach the door to our office space
        self.vpc.attach_internet_gateway(
            InternetGatewayId=self.internet_gateway.id
        )

        print("Internet Gateway created:", self.internet_gateway.id)
        return self.internet_gateway

    # ---------------- Subnet ----------------
    # This creates a specific room inside VPC
    def create_subnet(self, cidr="10.0.1.0/24", name="Kafka-Subnet-1"):
        self.subnet = self.ec2.create_subnet(
            CidrBlock=cidr,
            VpcId=self.vpc.id
        )

        # Make sure any computer we put in this room automatically gets an internet address
        self.subnet.meta.client.modify_subnet_attribute(
            SubnetId=self.subnet.id,
            MapPublicIpOnLaunch={'Value': True}
        )

        self.subnet.create_tags(
            Tags=[
                {
                    "Key": "Name",
                    "Value": name
                }
            ]
        )


        print("Subnet created:", self.subnet.id)
        return self.subnet

    # ---------------- Route Table ----------------
    # This creates a map that tells traffic how to get to the internet
    def create_route_table(self, name="Kafka-Route_Table-1"):
        self.route_table = self.vpc.create_route_table()

        self.route_table.create_route(
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=self.internet_gateway.id
        )

        # Connect this map to our specific subnet
        self.route_table.associate_with_subnet(
            SubnetId=self.subnet.id
        )

        self.route_table.create_tags(
            Tags=[
                {
                    "Key": "Name",
                    "Value": name
                }
            ]
        )


        print("Route Table created:", self.route_table.id)
        return self.route_table

    # ---------------- Security Group ----------------
    # This acts like a "security guard" that checks who is allowed to enter or leave
    def create_security_group(self, name="Kafka-Security-Group-1"):
        self.security_group = self.ec2.create_security_group(
            GroupName=name,
            Description="Security group for Kafka instances",
            VpcId=self.vpc.id
        )

        self.security_group.create_tags(
            Tags=[
                {
                    "Key": "Name",
                    "Value": name
                }
            ]
        )

        # Set the rules for the security guard:
        self.security_group.authorize_ingress(
            IpPermissions=[
                # Allow Remote access (SSH)
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
                },

                # Allow Kafka traffic
                {
                    "IpProtocol": "tcp",
                    "FromPort": 9092,
                    "ToPort": 9092,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
                },

                # Allow Zookeeper traffic 
                {
                    "IpProtocol": "tcp",
                    "FromPort": 2181,
                    "ToPort": 2181,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
                }
            ]
        )

        print("Security Group created:", self.security_group.id)
        return self.security_group

    # ---------------- User Data ----------------
    # This is a list of setup instructions for the EC2 instances to follow as soon as they turn on
    def get_user_data(self):
        return """#!/bin/bash
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
sleep 10

# 6. Configure Kafka to be reachable from the internet (important for testing!)
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "advertised.listeners=PLAINTEXT://$PUBLIC_IP:9092" >> config/server.properties

# 7. Start the Kafka server itself in the background
nohup bin/kafka-server-start.sh config/server.properties > kafka.log 2>&1 &
"""

    # ---------------- EC2 Instances ----------------
    # This starts up our virtual computers(servers) in subnet
    def launch_instances(self, ami="ami-0ed094fb1304fd857",
                         instance_type="t3.micro",
                         count=3):

        self.instances = self.ec2.create_instances(
            ImageId=ami,
            MinCount=count,
            MaxCount=count,
            InstanceType=instance_type,
            SubnetId=self.subnet.id,
            SecurityGroupIds=[self.security_group.id],
            UserData=self.get_user_data(), # Hand over the setup instructions
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": "Kafka-EC2"}]
                }
            ]
        )

        print("Launching EC2 instances...")

        # Wait for each computer to fully start up and get its internet address
        for instance in self.instances:
            instance.wait_until_running()
            instance.reload()

            print(f"Instance ID: {instance.id}")
            print(f"Public IP: {instance.public_ip_address}")
            print("-" * 40)

        print("Kafka Cluster Created Successfully")

    # ---------------- RUN ALL ----------------
    # This runs all the steps above in the correct order
    def deploy(self):
        self.create_vpc()
        self.create_internet_gateway()
        self.create_subnet()
        self.create_route_table()
        self.create_security_group()
        self.launch_instances()


# ---------------- MAIN EXECUTION ----------------
if __name__ == "__main__":
    # Prepare the building tools for the specific AWS location
    infra = KafkaAWSInfra(region="us-east-1")
    # Kick off the construction process
    infra.deploy()
