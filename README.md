# Kafka Cluster Infrastructure Setup

## Overview

This project provisions the infrastructure required to deploy an Apache Kafka cluster on AWS using Infrastructure as Code (IaC).

The deployment includes the following AWS resources:

* VPC
* Public and Private Subnets
* Internet Gateway
* Route Tables
* Security Groups
* EC2 Instances
* Apache Kafka Installation and Configuration
* AWS Secrets Manager Integration for Kafka Credentials

---

## Enhancements

The following improvements were made to the existing Kafka cluster infrastructure:

* Added automatic creation and retrieval of Kafka credentials using AWS Secrets Manager.
* Improved security by migrating Kafka instances from a public architecture to private subnets.
* Implemented secure access to instances using AWS Systems Manager (SSM).
* Reorganized the project structure to improve readability, maintainability, and scalability.
* Added CI/CD automation using GitHub Actions for infrastructure deployment.

---

## Deployment

Infrastructure changes are deployed automatically through GitHub Actions whenever code is pushed to the `develop` branch.

The deployment workflow performs the following steps:

1. Installs project dependencies.
2. Authenticates with AWS.
3. Synthesizes the CDK application.
4. Deploys the Kafka infrastructure stack.

---

## Architecture Components

* Amazon VPC
* Public Subnet (NAT Gateway)
* Private Subnet (Kafka Nodes)
* EC2 Instances
* Security Groups
* AWS Secrets Manager
* AWS Systems Manager (SSM)
* AWS CDK
* GitHub Actions
