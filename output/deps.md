```mermaid
graph LR
  service-a -->|GET| service-b
  service-c -->|GET| service-a
  service-d -->|GET| service-a
```