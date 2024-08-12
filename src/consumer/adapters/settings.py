import os

from dotenv import load_dotenv

load_dotenv()

# TODO Это просто отвратительно 🤮
config = {
    "Service": {
        "port": os.getenv("SERVICE_PORT") or 8080,
        "service_name": os.getenv("SERVICE_NAME"),
        "run_sleep_time": os.getenv("SERVICE_RUN_SLEEP_TIME"),
        "s3_dir": os.getenv("SERVICE_S3_DIR"),
        "content_type": os.getenv("SERVICE_CONTENT_TYPE"),
        "tmp_dir": os.getenv("SERVICE_TMP_DIR"),
        "consumers_number": os.getenv("SERVICE_CONSUMERS_NUMBER") or 10,
        "pool_size": os.getenv("SERVICE_POOL_SIZE") or 4,
        "graceful_shutdown_timeout": os.getenv("SERVICE_GRACEFUL_SHUTDOWN_TIMEOUT"),
        "readiness_interval": os.getenv("SERVICE_READINESS_INTERVAL"),
        "db_table": os.getenv("SERVICE_DB_TABLE"),
        "executor": os.getenv("SERVICE_EXECUTOR") or "thread",
    },
    "Model": {
        "model_path": os.getenv("MODEL_PATH", "consumer/data/clf_model/pose_clf_1"),
        "write_width": os.getenv("MODEL_WRITE_WIDTH") or 720,
        "write_height": os.getenv("MODEL_WRITE_HEIGHT") or 720,
        "bip_threshold": os.getenv("MODEL_BIP_THRESHOLD") or 0.1,
        "time_clf_threshold": os.getenv("MODEL_TIME_CLF_THRESHOLD") or 0.5,
        "frame_conf_count": os.getenv("MODEL_FRAME_CONF_COUNT") or 5,
    },
    "KafkaProducer": {
        "topic": os.getenv("KAFKA_PRODUCER_TOPIC"),
        "servers": os.getenv("KAFKA_SERVERS"),
        "ssl.ca.location": os.environ.get("KAFKA_SSL_CA_CERT_FILE"),
        "ssl.client.cert.location": os.environ.get("KAFKA_SSL_CLIENT_CERT_FILE"),
        "ssl.client.key.location": os.environ.get("KAFKA_SSL_CLIENT_KEY_FILE"),
        "sasl.username": os.environ.get("KAFKA_SASL_USERNAME"),
        "sasl.password": os.environ.get("KAFKA_SASL_PASSWORD"),
        "security_protocol": os.environ.get("KAFKA_SECURITY_PROTOCOL"),
        "sasl_mechanism": os.environ.get("KAFKA_SASL_MECHANISM"),
    },
    "KafkaConsumer": {
        "topic": os.getenv("KAFKA_CONSUMER_TOPIC"),
        "servers": os.getenv("KAFKA_SERVERS"),
        "consumer_group_id": os.getenv("KAFKA_CONSUMER_GROUP_ID"),
        "ssl.ca.location": os.environ.get("KAFKA_SSL_CA_CERT_FILE"),
        "ssl.client.cert.location": os.environ.get("KAFKA_SSL_CLIENT_CERT_FILE"),
        "ssl.client.key.location": os.environ.get("KAFKA_SSL_CLIENT_KEY_FILE"),
        "sasl.username": os.environ.get("KAFKA_SASL_USERNAME"),
        "sasl.password": os.environ.get("KAFKA_SASL_PASSWORD"),
        "security_protocol": os.environ.get("KAFKA_SECURITY_PROTOCOL"),
        "sasl_mechanism": os.environ.get("KAFKA_SASL_MECHANISM"),
        "consumer_batch_size": os.getenv("KAFKA_CONSUMER_BATCH_SIZE") or 10,
        "consumer_timeout_ms": os.getenv("KAFKA_CONSUMER_TIMEOUT_MS") or 1,
    },
    "Sentinel": {
        "host": os.environ.get("REDIS_SENTINEL_ENDPOINT"),
        "port": os.environ.get("REDIS_SENTINEL_PORT"),
        "redis_master_name": os.environ.get("REDIS_MASTER_NAME"),
        "redis_nodes": os.environ.get("REDIS_NODES"),
        "ttl": os.environ.get("REDIS_TTL") or 120,
        "socket_timeout": os.environ.get("REDIS_SOCKET_TIMEOUT") or 60,
        "password": os.environ.get("REDIS_PASSWORD"),
    },
    "Redis": {
        "host": os.environ.get("REDIS_HOST"),
        "port": os.environ.get("REDIS_PORT"),
        "username": os.environ.get("REDIS_USERNAME"),
        "password": os.environ.get("REDIS_PASSWORD"),
        "ttl": os.environ.get("REDIS_TTL") or 120,
    },
}
