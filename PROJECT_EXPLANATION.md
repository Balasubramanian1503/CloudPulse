# CloudPulse — Complete Project Explanation for Presentation

## 1. Project title
**CloudPulse: AWS Cloud Server Monitoring and Incident Management System**

## 2. What problem does it solve?
A cloud server may remain switched on while its CPU becomes overloaded. When CPU stays high, the application hosted on that server can become slow or unresponsive. Administrators need a simple way to inspect server metrics and keep track of warning events. CloudPulse provides a browser dashboard for that purpose.

## 3. What does the project do?
- Allows a user to register and sign in.
- Protects the monitoring dashboard and API routes behind login.
- Connects to Amazon CloudWatch through Boto3 when AWS mode is configured.
- Reads EC2 CPU utilization and EC2 status-check metrics.
- Displays CPU, memory (demo mode only unless CloudWatch Agent is configured), instance status, and metric source.
- Compares CPU usage against a configurable threshold (80% by default).
- Creates an incident when CPU reaches or exceeds the threshold.
- Stores user accounts, incidents, and metric history in SQLite.
- Provides a test-alert button to demonstrate incident recording.
- Provides demo mode for local testing without an AWS account.

**Important:** Demo mode generates simulated readings. AWS mode calls CloudWatch. Do not describe demo readings as real AWS measurements. The AWS code is ready to use, but you must configure credentials, region and your own EC2 instance ID and verify a successful request before claiming that you have demonstrated live AWS data.

## 4. Architecture and data flow

```text
User's browser
   |  HTML form / JavaScript fetch()
   v
Flask web application (app.py)
   |-- registration and login
   |-- session check on protected routes
   |-- JSON API endpoints
   |
   +--> monitor.py
          |-- demo_metrics() for local demo
          |-- aws_metrics() for live mode
                    |
                 Boto3 SDK
                    |
             Amazon CloudWatch
                    |
          EC2 CPU + status-check datapoints
   |
   +--> threshold comparison (CPU >= 80%)
   |
   +--> database.py --> SQLite database
                         |-- users
                         |-- metric_history
                         |-- incidents
   |
   v
JSON response --> dashboard.js --> cards, chart and incident table
```

### Step-by-step request lifecycle
1. A visitor opens `/`. Flask redirects the visitor to `/login` if there is no signed-in session.
2. The user creates an account at `/register`. The password is converted to a one-way password hash before it is stored.
3. On `/login`, the submitted password is checked against the saved hash. If it matches, Flask stores the user's ID and name in the session.
4. The user opens `/dashboard`. The `signed_in` decorator checks the session before rendering the dashboard.
5. `static/script.js` calls `/api/metrics` using `fetch()` every ten seconds.
6. The API calls `get_metrics()` in `monitor.py`. The `MONITOR_MODE` environment variable decides whether demo or AWS mode is used.
7. In AWS mode, Boto3 calls CloudWatch `GetMetricStatistics` for `CPUUtilization` and `StatusCheckFailed`, filtered by the configured EC2 instance ID.
8. Flask stores the returned sample in `metric_history`, compares CPU with `CPU_ALERT_THRESHOLD`, and writes an incident if the threshold is crossed.
9. The API returns JSON. JavaScript updates the dashboard cards, source notice, chart and incident table.

## 5. AWS services and concepts

### Amazon EC2
Elastic Compute Cloud provides virtual servers in AWS. The EC2 instance is the server being monitored. Each instance has an instance ID (for example, `i-0123456789abcdef0`) and runs in an AWS region.

### Amazon CloudWatch
CloudWatch collects and exposes monitoring metrics. This project reads `CPUUtilization` and `StatusCheckFailed` for the configured EC2 instance. The application requests the latest available five-minute datapoint within a recent time window.

### Boto3
Boto3 is the AWS SDK for Python. It lets the Flask backend call AWS APIs. The code creates a CloudWatch client and calls `get_metric_statistics()`.

### IAM
Identity and Access Management controls which AWS actions an identity can perform. The identity used by Boto3 needs permission to read the required CloudWatch metrics, including `cloudwatch:GetMetricStatistics`. Follow least privilege; do not use root credentials or hardcode access keys in Python files.

### Region
AWS services are accessed through regional endpoints. `AWS_DEFAULT_REGION` must match the region where the EC2 instance exists.

### Why is memory unavailable in AWS mode?
Standard EC2 CloudWatch metrics do not include guest operating-system RAM utilization. Install and configure the Amazon CloudWatch Agent on the EC2 instance, publish a metric such as `mem_used_percent`, and extend the Python query to retrieve it. The current demo mode simulates memory only.

## 6. Login and registration logic
- `/register` accepts name, email, password and confirmation.
- It checks that required fields are present, password length is at least eight characters, confirmation matches, and email is not already registered.
- `generate_password_hash()` hashes the password. Plain-text passwords are not stored.
- `/login` finds the account by email and `check_password_hash()` verifies the entered password.
- Successful login creates a Flask session containing the user ID and display name.
- The `signed_in` decorator protects the dashboard and JSON APIs.
- `/logout` clears the session.

This is a learning project, not production-grade identity management. Before public deployment, add CSRF protection, rate limiting, password reset, email verification, HTTPS, secure cookie settings, audit logging and stronger session controls.

## 7. Database design

### users
| Column | Meaning |
|---|---|
| id | Primary key for the user |
| name | Display name |
| email | Unique login email |
| password_hash | One-way password hash |
| created_at | Account creation timestamp |

### metric_history
| Column | Meaning |
|---|---|
| id | Primary key for a metric sample |
| cpu | CPU percentage returned by monitor |
| memory | Memory percentage if available |
| server_status | Status label |
| recorded_at | Timestamp of sample |

### incidents
| Column | Meaning |
|---|---|
| id | Primary key for incident |
| incident_type | For example HIGH_CPU or TEST_ALERT |
| message | Human-readable incident details |
| severity | Critical or Warning |
| created_at | Incident timestamp |

SQLite is file-based and convenient for a prototype. A production cloud application could use Amazon RDS for managed relational database storage.

## 8. CPU threshold logic
The threshold is read from `CPU_ALERT_THRESHOLD` in the `.env` file. The default is 80.

```python
if cpu >= threshold:
    add_incident(
        "HIGH_CPU",
        f"CPU utilization reached {cpu}%",
        "Critical"
    )
```

The current application checks the most recent incident to reduce repeat alerts during consecutive polling. A production solution should use a robust deduplication key, alert state transitions, evaluation windows, and incident resolution logic.

## 9. Explain each project file

- **app.py** — Entry point. Creates the Flask app, loads `.env`, initializes the database, defines register/login/logout routes, protects pages with a decorator, exposes JSON APIs, compares CPU to the threshold, and starts the local web server.
- **database.py** — Contains SQLite connection, table creation, user lookup/creation, incident storage, metric storage and read functions. It separates data access from web routing.
- **monitor.py** — Contains demo metric generation and AWS CloudWatch metric collection. `get_metrics()` chooses the correct monitoring mode.
- **requirements.txt** — Lists Flask, Boto3 and python-dotenv dependencies.
- **.env.example** — Template for application secret, mode, region, instance ID and threshold. Copy it to `.env`; do not commit `.env`.
- **templates/login.html** — Sign-in form.
- **templates/register.html** — Account creation form.
- **templates/index.html** — Main monitoring dashboard structure.
- **static/style.css** — Dashboard styling and responsive layout.
- **static/script.js** — Calls Flask APIs with `fetch()`, updates metric cards and the Chart.js line graph, and refreshes incidents.
- **cloudpulse.db** — Created automatically when the app first starts; stores local project data.

## 10. API endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/metrics` | GET | Collect metrics, save sample, evaluate threshold |
| `/api/incidents` | GET | Return latest incident records |
| `/api/history` | GET | Return stored metric samples |
| `/api/test-alert` | POST | Add a manual test incident |

All API endpoints require a signed-in session.

## 11. How to run on Windows

```powershell
# Open PowerShell in the extracted CloudPulse folder
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`, register a user, and sign in. The first run creates `cloudpulse.db` automatically. If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again.

## 12. Connect your own AWS account

1. Create or select an EC2 instance. Note its instance ID and region.
2. Configure AWS CLI credentials on the computer running CloudPulse with `aws configure`, or use an attached IAM role if the app is hosted on AWS.
3. Ensure the identity can call `cloudwatch:GetMetricStatistics` for the metrics being read.
4. Edit `.env` and set `MONITOR_MODE=aws`, `AWS_DEFAULT_REGION` and `EC2_INSTANCE_ID`.
5. Restart Flask and wait for CloudWatch datapoints to become available.
6. Check the dashboard notice. It should say AWS CloudWatch mode. If no datapoints appear, verify instance ID, region, credentials, permissions, and that the EC2 instance has been running long enough to publish metrics.

AWS resources may incur charges. Review current AWS pricing, use only resources you need, and stop or terminate test resources when finished. Do not share access keys or secret keys.

## 13. Honest current limitations
- One configured EC2 instance is supported.
- AWS mode reads CPU and status-check metrics only.
- AWS memory, disk and network monitoring are not implemented yet.
- No email/SMS notifications or automatic server remediation.
- SQLite is local to the application; it is not a managed multi-user cloud database.
- This project is intended as a learning prototype, not a production monitoring service.

## 14. Future enhancements
- Multi-instance monitoring and instance selection.
- CloudWatch Agent metrics for RAM and disk.
- Amazon SNS email/SMS notifications.
- Incident acknowledgement, assignment and resolution workflow.
- Amazon RDS for managed storage.
- Role-based access for administrator and viewer.
- Deployment on EC2 or Elastic Beanstalk behind HTTPS.
- Automated tests, CSRF protection, rate limiting and audit logs.

## 15. 90-second interview explanation

"My project is CloudPulse, an AWS cloud server monitoring and incident management system. The objective is to help an administrator monitor the performance and health of an EC2 server. I developed the web application using Python Flask, HTML, CSS and JavaScript, and I use SQLite to store user accounts, metric history and incidents. The application includes registration and login, and the monitoring dashboard and APIs are protected using a session-based login check. Passwords are stored as hashes rather than plain text.

For AWS integration, I use Amazon EC2 as the virtual server and Amazon CloudWatch as the monitoring service. I use Boto3, the AWS SDK for Python, to request CPU utilization and EC2 status-check metrics. The backend compares CPU utilization with a configurable threshold, which is 80 percent by default. When CPU reaches that threshold, it records an incident in SQLite. The frontend calls Flask API endpoints and displays the metrics, a CPU trend chart and incident history. I also implemented a demo mode for testing without AWS credentials. In AWS mode, the application retrieves actual CloudWatch datapoints for the EC2 instance configured by the user."

Only say that you personally connected and tested live AWS if you have completed those steps successfully. Otherwise say: "I implemented the AWS integration path and am validating it with my EC2 configuration; the demo mode lets me test the dashboard independently."

## 16. Interview questions and answers

**What is EC2?** Amazon Elastic Compute Cloud is a service that provides virtual servers in AWS.

**What is CloudWatch?** It is AWS's monitoring and observability service. It collects metrics and logs and can trigger alarms.

**Why Boto3?** Boto3 is the AWS SDK for Python. It lets my Flask backend call CloudWatch APIs programmatically.

**What is IAM?** IAM controls authentication and authorization for AWS resources. It lets me grant the application only the required permissions.

**What is an API?** An API is a defined interface that allows software components to communicate. The browser calls Flask endpoints and receives JSON.

**What is JSON?** A lightweight text format for transferring structured data between applications.

**What happens when CPU reaches 85%?** The backend compares 85 with the configured 80% threshold and stores a high-CPU incident. The dashboard then shows it in the incident list.

**Does it automatically fix high CPU?** No. The current version detects and records the issue. Automated remediation is a possible future enhancement and would need safeguards.

**Why SQLite?** It is lightweight and does not require a separate database server, which makes it suitable for a prototype. For production I would consider Amazon RDS.

**How are passwords protected?** Werkzeug's password hashing functions store a hash, not the original password.

**Why isn't memory shown for AWS?** Standard EC2 metrics do not include guest RAM. The CloudWatch Agent must publish a custom memory metric first.

**What would you add next?** Multiple EC2 instances, RAM and disk metrics, SNS notifications, incident resolution, Amazon RDS and production security controls.
