# SRE Observability Lab

A hands-on Site Reliability Engineering (SRE) project demonstrating application monitoring, observability, alerting, Kubernetes deployment, and autoscaling.

The project runs a FastAPI service instrumented with Prometheus metrics, visualized through Grafana dashboards, and monitored using SLO-based alert rules. It also includes a Jenkins CI/CD pipeline, Kubernetes manifests, and optional Terraform configuration for Google Kubernetes Engine (GKE).

Fault injection is supported through the `POST /chaos` endpoint to simulate service errors and latency during incident-response exercises.

## Tech Stack

- **Backend:** Python, FastAPI
- **Containerization:** Docker, Docker Compose
- **Monitoring:** Prometheus
- **Visualization:** Grafana
- **Orchestration:** Kubernetes, Kind, kubectl
- **Autoscaling:** Horizontal Pod Autoscaler (HPA), Metrics Server
- **CI/CD:** Jenkins, Jenkinsfile
- **Infrastructure as Code:** Terraform (optional GKE deployment)
- **Testing:** pytest, shell scripts

## Architecture

1. FastAPI exposes application endpoints and Prometheus metrics.
2. Docker packages the application into a container.
3. Prometheus collects metrics and evaluates alerting rules.
4. Grafana visualizes request rate, errors, and latency.
5. Kubernetes manages application replicas and performs health checks.
6. HPA adjusts the number of replicas based on CPU utilization.
7. Jenkins defines a pipeline for automating build and test stages.

## Run Locally with Docker Compose

Start the application, Prometheus, and Grafana:

```bash
docker compose up --build -d
```

Generate traffic:

```bash
chmod +x scripts/loadtest.sh
./scripts/loadtest.sh 300 &
```

Open the following endpoints:

- **Application:** http://localhost:8000/orders
- **Application metrics:** http://localhost:8000/metrics
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000

In Grafana, open the `orders-service - RED metrics` dashboard. Check request rate, error rate, and latency visualizations.

## Incident Simulation and Alerting

Use the following commands to simulate incidents.

### 1. Simulate a high error rate

```bash
curl -X POST http://localhost:8000/chaos \
  -H 'Content-Type: application/json' \
  -d '{"error_rate":0.3,"latency_ms":0}'
```

### 2. Simulate high latency

```bash
curl -X POST http://localhost:8000/chaos \
  -H 'Content-Type: application/json' \
  -d '{"error_rate":0,"latency_ms":800}'
```

### 3. Restore normal behavior

```bash
curl -X POST http://localhost:8000/chaos \
  -H 'Content-Type: application/json' \
  -d '{"error_rate":0,"latency_ms":0}'
```

Prometheus alert rules include:

- `HighErrorRate` — triggers when the error ratio exceeds the configured threshold.
- `HighP95Latency` — triggers when the 95th-percentile latency exceeds the configured threshold.
- `ServiceDown` — detects when the monitored service is unavailable.

Review the active alerts in Prometheus and correlate them with the Grafana dashboard.

## Kubernetes Deployment with Kind

Create a local Kubernetes cluster:

```bash
kind create cluster --name sre-lab
```

Build the application image and load it into Kind:

```bash
docker build -t orders-service:local app/
kind load docker-image orders-service:local --name sre-lab
```

Deploy the application:

```bash
sed 's|IMAGE_PLACEHOLDER|orders-service:local|g' k8s/deployment.yaml | kubectl apply -f -
```

Check deployment status:

```bash
kubectl rollout status deployment/orders-service
kubectl get pods
kubectl get services
kubectl get hpa
```

The Kubernetes configuration includes:

- Two initial application replicas.
- Readiness and liveness probes.
- CPU and memory requests and limits.
- A ClusterIP service.
- An HPA targeting 60% average CPU utilization, with a minimum of two and maximum of six replicas.

### Verified Autoscaling Test

The HPA was tested in a local Kind cluster by generating CPU load.

- Started with **2 replicas**.
- Scaled up to **4 replicas**, then **6 replicas** under increased CPU utilization.
- After stopping the load, CPU utilization returned to approximately 3–4%.
- The HPA scaled back down to **2 replicas**.

The final deployment returned to two available pods, demonstrating the scale-up and scale-down behavior of the HPA.

## Runbook: HighErrorRate

1. Open Grafana and identify when the error ratio increased.
2. Check recent deployment history:

   ```bash
   kubectl rollout history deployment/orders-service
   ```

3. Inspect application logs:

   ```bash
   kubectl logs -l app=orders-service --tail=100
   ```

4. If a deployment is identified as the cause and rollback is appropriate, run:

   ```bash
   kubectl rollout undo deployment/orders-service
   ```

5. Document the incident timeline, root cause, mitigation, and follow-up actions.

## Runbook: HighP95Latency

1. Review request latency and in-flight requests in Grafana.
2. Check CPU utilization and HPA status:

   ```bash
   kubectl top pods
   kubectl get hpa
   ```

3. Investigate CPU pressure, slow dependencies, and recent application changes.
4. If additional capacity is appropriate, scale the deployment:

   ```bash
   kubectl scale deployment/orders-service --replicas=6
   ```

5. Verify that latency improves and review whether autoscaling thresholds need adjustment.

## Tests

Run the application tests using the project's Python virtual environment:

```bash
cd app
source .venv/bin/activate
pytest -v
```

The four application tests passed in the local test run:

- Health endpoint
- Orders endpoint
- Fault-injection behavior
- Prometheus metrics endpoint

## Optional GCP / Terraform Deployment

Terraform configuration for GKE is included as an optional extension. Cloud infrastructure was not provisioned as part of the local demonstration.

To explore the Terraform configuration, configure your Google Cloud project and credentials first, then review the resources and estimated costs before applying any changes.

```bash
cd terraform
terraform init
terraform validate
terraform plan -var="project_id=YOUR_PROJECT_ID"
```

Only run `terraform apply` if you intentionally want to provision cloud resources and understand the associated costs.

## Current Scope and Future Improvements

- Add Kubernetes-native service discovery for Prometheus.
- Connect Jenkins to an end-to-end build, test, and deployment workflow.
- Add repeatable load tests and performance comparisons.
- Add screenshots of the Grafana dashboard, Prometheus alerts, and HPA scaling.
- Extend automated checks for the Kubernetes manifests and CI/CD pipeline.

This project was tested locally using Docker Compose and a Kind Kubernetes cluster. GCP deployment is optional and has not been claimed as completed.