```mermaid
graph LR
  service-a -->|GET| service-b
  service-a -->|GET| service-e
  service-c -->|GET| service-a
  service-d -->|GET| service-a
```