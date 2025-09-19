# Floy Technical Challenge

## Questions

**1. What were the reasons for your choice of API/protocol/architectural style used for the client-server communication?**

API - FastAPI: A fast, simple and high-performing API framework. For this simple prototype implementation, it
was the best tool.

FastAPI + JSON over HTTP: The easy fast route.
Alternatives could be: Django/Flask or gRPC or message queues[no API framework]. The latter two could be better alternatives for a cloud implementation.

Asyncronhous setup: to mimick real-life I/O bound handling, the buffer [deque] has O(1) complexity (the pop operation).
To simplify the scenario, a manual debouncing logic (harcoded threshold) is used. Not translatable to an actual implemention, for this: an exponential weighted average (of inter-arrival times) could be calculated and the timeout can be set based on this.

Database - SQLite: Since we are dealing with a small amount of sample data, SQLite is sufficient. SQLite is serverless, which is easier to integrate into the existing app. When extending this to the real-world scenario of much larger datasets, I would switch to PostgreSQL, since it can scale easily.


**2.  As the client and server communicate over the internet in the real world, what measures would you take to secure the data transmission and how would you implement them?**

- TLS (transport layer security)
- Authentication: for HTTPS: OAuth/API Keys
- Cloud Implementation: [Example: AWS Services]
    * VPC - private subnets for the client/server/DB
    * Security groups - port restrictions
    * KMS to manage encryption at rest.
    * CloudWatch