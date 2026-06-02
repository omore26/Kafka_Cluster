import os
from aws_cdk import (
    Stack,
    CfnOutput,
    Tags,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    RemovalPolicy,
)
from constructs import Construct
import config
import requests

class KafkaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        name_prefix = config.PROJECT_NAME
        
        # VPC with public subnet for nat and private subnets for kafka nodes
        self.vpc = ec2.Vpc(
            self, "KafkaVpc",
            vpc_name=f"{name_prefix}-VPC",
            ip_addresses=ec2.IpAddresses.cidr(config.VPC_CIDR),
            enable_dns_hostnames=True,
            enable_dns_support=True,
            nat_gateways=1,
            max_azs=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name=f"{name_prefix}-Public-Subnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name=f"{name_prefix}-Private-Subnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        Tags.of(self.vpc).add("Name", f"{name_prefix}-VPC")

        # Security Rules for Kafka cluster communication
        self.security_group = ec2.SecurityGroup(
            self, "KafkaSecurityGroup",
            vpc=self.vpc,
            security_group_name=f"{name_prefix}-SG",
            description="Security group for Kafka instances",
            allow_all_outbound=True
        )
        Tags.of(self.security_group).add("Name", f"{name_prefix}-SG")

        my_ip = requests.get(
            "https://checkip.amazonaws.com",
            timeout = 5
        ).text.strip()

        # Allow SSH access only from the specified IP in the config
        self.security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(f"{my_ip}/32"),
            connection=ec2.Port.tcp(config.SSH_PORT),
            description="Allow SSH access from allowed IP"
        )

        # Allow internal Kafka traffic
        self.security_group.add_ingress_rule(
            peer=self.security_group,
            connection=ec2.Port.tcp(config.KAFKA_PORT),
            description="Allow Kafka traffic within the security group"
        )

        # Allow internal Zookeeper traffic
        self.security_group.add_ingress_rule(
            peer=self.security_group,
            connection=ec2.Port.tcp(config.ZOOKEEPER_PORT),
            description="Allow Zookeeper traffic within the security group"
        )

        # Store kafka credentials centrally
        self.secret = secretsmanager.Secret(
            self,
            "KafkaSecret",
            secret_name = f"{name_prefix}-Credentials",
            description="Kafka credentials used by EC2",
            generate_secret_string = secretsmanager.SecretStringGenerator(
                secret_string_template = '{"kafka_username":"kafkaadmin"}',
                generate_string_key = "kafka_password",
                exclude_punctuation = True,
            ),
            removal_policy = RemovalPolicy.DESTROY,
        )

        # Role for SSM Access and secret retrieval
        self.role = iam.Role(
            self, "KafkaEC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )
        
        # Add AWS SSM Managed Instance Core policy to allow secure connection to private instances
        self.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
        )
        
        self.secret.grant_read(self.role)

        # Load startup script
        user_data_path = os.path.join(os.path.dirname(__file__), "..", "Scripts", "user_data.sh")
        with open(user_data_path, "r") as f:
            user_data_template = f.read()

        # Launch Instaces
        self.instances = []
        for i in range(config.INSTANCE_COUNT):
            user_data_content = user_data_template.replace("DYNAMIC_SECRET_NAME", self.secret.secret_name)
            ud = ec2.UserData.custom(user_data_content)

            instance = ec2.Instance(
                self, f"KafkaInstance{i+1}",
                instance_name=f"{name_prefix}-EC2-{i+1}",
                instance_type=ec2.InstanceType(config.INSTANCE_TYPE),
                machine_image=ec2.MachineImage.latest_amazon_linux2023(),
                vpc=self.vpc,

                # Launch instances in the private subnet
                vpc_subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ),
                security_group=self.security_group,
                role=self.role,
                user_data=ud
            )
            self.instances.append(instance)

            CfnOutput(
                self, f"Node{i+1}PrivateIP",
                value=instance.instance_private_ip,
                description=f"The Private IP Address of Node {i+1}"
            )
