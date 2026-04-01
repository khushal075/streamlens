docker exec -it streamlens-kafka \
kafka-topics --create \
--topic logs \
--bootstrap-server localhost:9092 \
--partitions 3 \
--replication-factor 1