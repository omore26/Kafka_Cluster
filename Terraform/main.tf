# Telling Terraform we want to work with AWS and where (region) to build everything
provider "aws" {
    region = var.region
}

# 2. Creating a VPC for our project
resource "aws_vpc" "main_vpc" {
    cidr_block = var.vpc_cidr

    tags = {
      Name = "Kafka-VPC-1"
    }
}

# Creating a specific Subnet inside our office space for our servers
resource "aws_subnet" "public_subnet" {
    vpc_id = aws_vpc.main_vpc.id

    cidr_block = var.subnet_cidr

    availability_zone = var.availability_zone

    map_public_ip_on_launch = true

    tags = {
      Name = "Kafka-Public-Subnet-1"
    }
}

# 4. Building a Internet Gateway so our setup can connect to the internet
resource "aws_internet_gateway" "igw" {
    vpc_id = aws_vpc.main_vpc.id

    tags = {
      Name = "Kafka_IGW-1"
    }  
}

# 5. Creating a Route Table to help traffic 
resource "aws_route_table" "public_route_table" {
    vpc_id = aws_vpc.main_vpc.id

    route {
        cidr_block = "0.0.0.0/0"

        gateway_id = aws_internet_gateway.igw.id
    }

    tags = {
        Name = "Kafka_Route_Table_1"
    }
}

# Handing the map to the Subnet so everyone inside knows how to get out
resource "aws_route_table_association" "route_association" {
    subnet_id = aws_subnet.public_subnet.id
    route_table_id = aws_route_table.public_route_table.id
}


# 7. Setting up a Security Group to check who is allowed in
resource "aws_security_group" "kafka_sg" {

    name = "Kafka_SG"

    vpc_id = aws_vpc.main_vpc.id

    # Allow "Remote Control" access (SSH)
    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = [ "0.0.0.0/0" ]
    }

    # Allow Kafka traffic (where the data flows)
    ingress {
        from_port = 9092
        to_port = 9092
        protocol = "tcp"
        cidr_blocks = [ "0.0.0.0/0" ]
    }

    # Allow Zookeeper traffic (the manager for Kafka)
    ingress {
        from_port = 2181
        to_port = 2181
        protocol = "tcp"
        cidr_blocks = [ "0.0.0.0/0" ]
    }

    # Outbound Rule: Allow everything inside to talk to the outside world
    egress {
        from_port = 0

        to_port = 0

        protocol = "-1"
        
        cidr_blocks = [ "0.0.0.0/0" ]
    }
}

# Ordering the first virtual computer (Server), putting it in our room, and giving it setup instructions
resource "aws_instance" "kafka_1" {

    ami = var.ami
    instance_type = var.instance_type
    subnet_id = aws_subnet.public_subnet.id
    vpc_security_group_ids = [ 
        aws_security_group.kafka_sg.id
    ]

    # Run the setup script (install Kafka/Java) as soon as it turns on
    user_data = file(var.user_data_script)

    tags = {
      Name = "Kafka_EC2_1"
    }
}


# Ordering the second virtual computer
resource "aws_instance" "kafka_2" {

    ami = var.ami
    instance_type = var.instance_type
    subnet_id = aws_subnet.public_subnet.id
    vpc_security_group_ids = [ 
        aws_security_group.kafka_sg.id
    ]

    user_data = file(var.user_data_script)

    tags = {
      Name = "Kafka_EC2_2"
    }
}


# 10. Ordering the third virtual computer
resource "aws_instance" "kafka_3" {

    ami = var.ami
    instance_type = var.instance_type
    subnet_id = aws_subnet.public_subnet.id
    vpc_security_group_ids = [ 
        aws_security_group.kafka_sg.id
    ]

    user_data = file(var.user_data_script)

    tags = {
      Name = "Kafka_EC2_3"
    }
}
