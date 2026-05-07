# Where in the world (AWS Region) we want to build our setup
variable "region" {
  type    = string
}

# The total size of our private "digital office space" (Network range)
variable "vpc_cidr" {
  type = string
}

# The size of the specific Subnet
variable "subnet_cidr" {
  type = string
}

# The specific section within the region for extra safety (Availability Zone)
variable "availability_zone" {
  type = string
}

# The "template" for the computer's operating system (AMI)
variable "ami" {
  type    = string
}

# The "size" and "power" of the virtual computer we are renting (Instance Type)
variable "instance_type" {
  type    = string
}

# The name tag for our Security Group
variable "security_group_name" {
  type    = string
}

# The path to the file that contains our computer's setup instructions
variable "user_data_script" {
  type    = string
}
