```mermaid
graph LR
  service-a -->|GET| service-b
  service-a -->|GET| service-c
  service-a -->|GET| service-e
  service-b -->|GET| service-a
  service-c -->|GET| service-a
  service-c -->|POST| service-a
  service-d -->|GET| service-a
  service-d -->|GET| service-c
  service-d -->|POST| service-c
  service-e -->|GET| service-c
```