package main

deny contains msg if {
    resource := input.Resources[_]
    resource.Type == "AWS::EC2::SecurityGroup"
    rule := resource.Properties.SecurityGroupIngress[_]
    rule.CidrIp == "0.0.0.0/0"
    rule.FromPort == 22
    msg := "SSH port 22 must not be open to the internet."
}

deny contains msg if {
    resource := input.Resources[_]
    resource.Type == "AWS::EC2::SecurityGroupIngress"
    resource.Properties.CidrIp == "0.0.0.0/0"
    resource.Properties.FromPort == 22
    msg := "SSH port 22 must not be open to the internet."
}

deny contains msg if {
    resource := input.Resources[_]
    resource.Type == "AWS::EC2::SecurityGroup"
    rule := resource.Properties.SecurityGroupIngress[_]
    rule.CidrIp == "0.0.0.0/0"
    rule.FromPort == 9092
    msg := "Kafka port 9092 must not be open to the internet."
}

deny contains msg if {
    resource := input.Resources[_]
    resource.Type == "AWS::EC2::SecurityGroupIngress"
    resource.Properties.CidrIp == "0.0.0.0/0"
    resource.Properties.FromPort == 9092
    msg := "Kafka port 9092 must not be open to the internet."
}

deny contains msg if {
    resource := input.Resources[_]
    resource.Type == "AWS::EC2::SecurityGroup"
    rule := resource.Properties.SecurityGroupIngress[_]
    rule.CidrIp == "0.0.0.0/0"
    rule.FromPort == 2181
    msg := "Zookeeper port 2181 must not be open to the internet."
}

deny contains msg if {
    resource := input.Resources[_]
    resource.Type == "AWS::EC2::SecurityGroupIngress"
    resource.Properties.CidrIp == "0.0.0.0/0"
    resource.Properties.FromPort == 2181
    msg := "Zookeeper port 2181 must not be open to the internet."
}

deny contains msg if {
    resource := input.Resources[_]
    resource.Type == "AWS::EC2::Instance"

    subnet_id := resource.Properties.SubnetId.Ref

    not contains(subnet_id, "Private")

    msg := "Kafka EC2 instances must be launched in private subnets."
}

deny contains msg if {
    resource := input.Resources[_]
    resource.Type == "AWS::SecretsManager::Secret"
    not resource.Properties.GenerateSecretString
    msg := "Kafka credentials must be generated through Secrets Manager, not hardcoded."
}