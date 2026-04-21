```mermaid
graph LR
classDef First_project fill:#90EE90,stroke:#333,color:#000
classDef Kafka fill:#FFB6C1,stroke:#333,color:#000
classDef Repo-1 fill:#87CEEB,stroke:#333,color:#000
classDef Repo-2 fill:#FFD700,stroke:#333,color:#000

  Kafka:order-created-bd["Kafka:order-created-bd
(Kafka)"]
  Kafka:topic-A["Kafka:topic-A
(Kafka)"]
  service-a["service-a
(First_project)"]
  service-b["service-b
(First_project)"]
  service-c["service-c
(First_project)"]
  service-d["service-d
(First_project)"]
  service-e["service-e
(First_project)"]
  service-f["service-f
(Repo-1)"]
  service-g["service-g
(Repo-2)"]

  service-a -->|GET /items| service-b
  service-a -->|GET /items| service-c
  service-a -->|GET /health| service-e
  service-a -->|GET /get-from-g| service-g
  service-a -->|GET /status| service-f
  service-b -->|GET /monitoring| service-a
  service-b -->|KAFKA_PRODUCER| Kafka:order-created-bd
  service-c -->|GET /call-a| service-a
  service-c -->|POST /post-data| service-a
  service-d -->|GET /call-a| service-a
  service-d -->|GET /addressdetails| service-c
  Kafka:order-created-bd -->|KAFKA_CONSUMER| service-d
  service-e -->|GET /credentials| service-c
  service-f -->|KAFKA_PRODUCER| Kafka:topic-A
  Kafka:topic-A -->|KAFKA_CONSUMER| service-g
class service-a,service-b,service-c,service-d,service-e First_project
class Kafka:order-created-bd,Kafka:topic-A Kafka
class net8.0,service-f Repo-1
class service-g Repo-2
```