from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
from confluent_kafka.schema_registry.avro import AvroSerializer

schema_registry_conf = {"url": "http://localhost:8081"}
client = SchemaRegistryClient(schema_registry_conf)

def validate_message(topic: str, message: dict):
    # Fetch latest schema
    schema_obj = client.get_latest_version(f"{topic}-value").schema
    serializer = AvroSerializer(schema_obj, client)
    # If invalid, raises exception
    serializer.encode(message, None)