import boto3
import config
import json
import time


# This class acts as a blueprint to build our Kafka setup on AWS from scratch
class KafkaAWSInfra:
    def __init__(self):
        # We start by picking which AWS "location" (region) we want to build in
        self.ec2 = boto3.resource("ec2", region_name=config.REGION)
        self.client = boto3.client("ec2", region_name=config.REGION)
        self.secrets_client = boto3.client("secretsmanager", region_name=config.REGION)
        self.iam_client = boto3.client("iam", region_name=config.REGION)

        # These are placeholders where we'll store the IDs of the parts we build
        self.vpc = None
        self.internet_gateway = None
        self.subnet = None
        self.route_table = None
        self.security_group = None
        self.instances = []
        self.secret_arn = None
        self.instance_profile_name = None

    # ---------------- VPC ----------------
    # This creates a private space for our project to live in
    def create_vpc(self):
        self.vpc = self.ec2.create_vpc(CidrBlock=config.VPC_CIDR)
        self.vpc.wait_until_available() 

        # Enable features so our computers can have easy-to-read names instead of just numbers
        self.vpc.modify_attribute(EnableDnsSupport={'Value': True})
        self.vpc.modify_attribute(EnableDnsHostnames={'Value': True})

        self.vpc.create_tags(Tags=[{"Key": "Name", "Value": config.VPC_NAME}])

        print("VPC created:", self.vpc.id)
        return self.vpc

    # ---------------- Internet Gateway ----------------
    # This builds a "front door" for our private space so it can connect to the internet
    def create_internet_gateway(self):
        self.internet_gateway = self.ec2.create_internet_gateway()
        self.internet_gateway.create_tags(
            Tags = [
                {
                    "Key":"Name",
                    "Value":config.IGW_NAME
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
    def create_subnet(self):
        self.subnet = self.ec2.create_subnet(
            CidrBlock=config.SUBNET_CIDR,
            VpcId=self.vpc.id
        )

        # Make sure any computer we put in this room automatically gets an internet address
        self.subnet.meta.client.modify_subnet_attribute(
            SubnetId=self.subnet.id,
            MapPublicIpOnLaunch={'Value': False}
        )

        self.subnet.create_tags(
            Tags=[
                {
                    "Key": "Name",
                    "Value": config.SUBNET_NAME
                }
            ]
        )


        print("Subnet created:", self.subnet.id)
        return self.subnet

    # ---------------- Route Table ----------------
    # This creates a map that tells traffic how to get to the internet
    def create_route_table(self):
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
                    "Value": config.ROUTE_TABLE_NAME
                }
            ]
        )


        print("Route Table created:", self.route_table.id)
        return self.route_table

    # ---------------- Security Group ----------------
    # This acts like a "security guard" that checks who is allowed to enter or leave
    def create_security_group(self):
        self.security_group = self.ec2.create_security_group(
            GroupName=config.SECURITY_GROUP_NAME,
            Description="Security group for Kafka instances",
            VpcId=self.vpc.id
        )

        self.security_group.create_tags(
            Tags=[
                {
                    "Key": "Name",
                    "Value": config.SECURITY_GROUP_NAME
                }
            ]
        )

        # Set the rules for the security guard:
        self.security_group.authorize_ingress(
            IpPermissions=[
                # Allow Remote access (SSH)
                {
                    "IpProtocol": "tcp",
                    "FromPort": config.SSH_PORT,
                    "ToPort": config.SSH_PORT,
                    "IpRanges": [{"CidrIp": config.ALLOWED_IP}]
                },

                # Allow Kafka traffic
                {
                    "IpProtocol": "tcp",
                    "FromPort": config.KAFKA_PORT,
                    "ToPort": config.KAFKA_PORT,
                    "UserIdGroupPairs": [{"GroupId": self.security_group.id}]
                },

                # Allow Zookeeper traffic 
                {
                    "IpProtocol": "tcp",
                    "FromPort": config.ZOOKEEPER_PORT,
                    "ToPort": config.ZOOKEEPER_PORT,
                    "UserIdGroupPairs": [{"GroupId": self.security_group.id}]
                }
            ]
        )

        print("Security Group created:", self.security_group.id)
        return self.security_group

    # ---------------- User Data ----------------
    # This is a list of setup instructions for the EC2 instances to follow as soon as they turn on
    def get_user_data(self):
        with open("user_data.sh", "r") as file:
            return file.read()
    
    # ---------------- Secret Manager ---------------
    def create_kafka_secret(self):
        secret_value = {
            "kafka_username": config.KAFKA_USERNAME,
            "kafka_password": config.KAFKA_PASSWORD
        }

        response = self.secrets_client.create_secret(
            Name = config.KAFKA_SECRET_NAME,
            Description = "Kafka credentials used by EC2",
            SecretString = json.dumps(secret_value)
        )

        self.secret_arn = response["ARN"]

        print("Kafka Secret Created:", self.secret_arn)
        return self.secret_arn
    
    # ---------------- IAM Role ---------------------

    def create_ec2_role(self):
        role_name = config.EC2_ROLE_NAME
        self.instance_profile_name = config.INSTANCE_PROFILE_NAME

        role_policy = {
            "Version" : "2012-10-17",
            "Statement" : [
                {
                    "Effect":"Allow",
                    "Principal":{
                        "Service" : "ec2.amazonaws.com",
                    },
                    "Action" : "sts:AssumeRole"
                }
            ]
        }

        self.iam_client.create_role(
            RoleName = role_name,
            AssumeRolePolicyDocument = json.dumps(role_policy)
        )

        policy_document = {
            "Version" : "2012-10-17",
            "Statement" : [
                {
                    "Effect" : "Allow",
                    "Action" : [
                        "secretemanager:GetSecretValue"
                    ],
                    "Resource":self.secret_arn
                }
            ]
        }

        self.iam_client.put_role_policy(
            RoleName = role_name,
            PolicyName = "KafkaSecretReadPolicy",
            PolicyDocument  = json.dumps(policy_document)
        )

        self.iam_client.create_instance_profile(
            InstanceProfileName = self.instance_profile_name
        )

        self.iam_client.add_role_to_instance_profile(
            InstanceProfileName = self.instance_profile_name,
            RoleName = role_name
        )

        time.sleep(10)

        print("EC2 IAM Role and Instance profile created.")

    # ---------------- EC2 Instances ----------------
    # This starts up our virtual computers(servers) in subnet
    def launch_instances(self):

        self.instances = self.ec2.create_instances(
            ImageId=config.AMI_ID,
            MinCount=config.INSTANCE_COUNT,
            MaxCount=config.INSTANCE_COUNT,
            InstanceType=config.INSTANCE_TYPE,
            SubnetId=self.subnet.id,
            SecurityGroupIds=[self.security_group.id],
            IamInstanceProfile = {
                "Name" : self.instance_profile_name
            },
            UserData=self.get_user_data(), # Hand over the setup instructions
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": config.INSTANCE_NAME}]
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
        
        self.create_kafka_secret()
        self.create_ec2_role()

        self.launch_instances()


