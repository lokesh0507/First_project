```mermaid
graph LR
classDef Kafka fill:#FFB6C1,stroke:#333,color:#000
classDef allegion_iot_repo_0 fill:#E0E084,stroke:#333,color:#000
classDef repo_1_iot fill:#84C5E0,stroke:#333,color:#000
classDef repo_2_iot fill:#90E084,stroke:#333,color:#000

  Kafka_order_created_bd["Kafka:order-created-bd
(Kafka)"]
  Kafka_topic_A["Kafka:topic-A
(Kafka)"]
  service_a["service-a
(allegion.iot.repo-0)"]
  service_b["service-b
(allegion.iot.repo-0)"]
  service_c["service-c
(allegion.iot.repo-0)"]
  service_d["service-d
(allegion.iot.repo-0)"]
  service_e["service-e
(allegion.iot.repo-0)"]
  service_f["service-f
(repo-1.iot)"]
  service_g["service-g
(repo-2.iot)"]

  service_e -->|GET /credentials| service_c
  service_d -->|GET /call-a| service_a
  service_d -->|GET /addressdetails| service_c
  service_a -->|GET /items| service_b
  service_a -->|GET /items| service_c
  service_a -->|GET /health| service_e
  service_a -->|GET /get-from-g| service_g
  service_a -->|GET /status| service_f
  service_c -->|GET /call-a| service_a
  service_c -->|POST /post-data| service_a
  service_b -->|GET /monitoring| service_a
  Kafka_order_created_bd -->|"KAFKA_CONSUMER<br/>Events Consuming:<br/>• OrderCreatedEvent"| service_d
  service_b -->|"KAFKA_PRODUCER<br/>Events Producing:<br/>• OrderCreatedEvent<br/>• PaymentInitiatedEvent"| Kafka_order_created_bd
  Kafka_topic_A -->|"KAFKA_CONSUMER<br/>Events Consuming:<br/>• TopicAEvent"| service_g
  service_f -->|"KAFKA_PRODUCER<br/>Events Producing:<br/>• TopicAEvent"| Kafka_topic_A

class Kafka_order_created_bd,Kafka_topic_A Kafka
class service_a,service_b,service_c,service_d,service_e allegion_iot_repo_0
class service_f repo_1_iot
class service_g repo_2_iot
```