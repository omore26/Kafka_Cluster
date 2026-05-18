from Kafka_New import KafkaAWSInfra

# ---------------- MAIN EXECUTION ----------------
if __name__ == "__main__":
    # Prepare the building tools for the specific AWS location
    infra = KafkaAWSInfra()
    # Kick off the construction process
    infra.deploy()
