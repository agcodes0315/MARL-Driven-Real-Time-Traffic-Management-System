# 🚦 MARL-Driven Real-Time Traffic Management System

### Adaptive traffic control, traffic forecasting and secure inter-agent communication

A SUMO-based traffic management project combining **multi-agent adaptive signal control, LSTM-based demand forecasting, emergency vehicle prioritization and secure communication between traffic agents**.

[![Repository](https://img.shields.io/badge/GitHub-Repository-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/agcodes0315/MARL-Driven-Real-Time-Traffic-Management-System)
[![Patent](https://img.shields.io/badge/Patent-202511108091%20A-2563EB?style=flat-square&logo=googledrive&logoColor=white)](https://drive.google.com/file/d/1QSSDN_fmPc41MEugw1atImfDk9ymtrHb/view?usp=sharing)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Security Tests](https://img.shields.io/badge/Security%20Tests-17%20Passing-2EA44F?style=flat-square&logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-222222?style=flat-square)

`Python` `SUMO` `TraCI` `LSTM` `Multi-Agent Systems` `TLS 1.3` `X.509` `RSA-PSS`

## 🚀 What This Project Does

The project explores whether traffic signals can respond to changing road conditions instead of relying only on fixed timing plans.

Each controlled intersection acts as a traffic agent inside **SUMO**. Python communicates with the simulation through **TraCI**, allowing the controller to observe traffic conditions and adapt signal behaviour during execution.

The system also includes:

- LSTM-based traffic demand forecasting
- emergency vehicle prioritization
- comparison against a rule-based baseline
- TLS 1.3 mutual authentication
- X.509 identities for traffic agents
- RSA-PSS signed messages
- SHA-256 integrity validation
- replay protection using timestamps and nonces
- automated security tests
- executable adversarial scenarios

The traffic-control layer and security layer are intentionally separated so that network messages are validated before they influence a signal decision.

## 📊 Results

The adaptive controller was compared against the project's rule-based traffic-control baseline in SUMO.

| Metric | Rule-Based Baseline | Adaptive System | Change |
|---|---:|---:|---:|
| Average waiting time | 55 s | 32 s | **41.8% lower** |
| Queue length | 30 vehicles | 15 vehicles | **50% lower** |
| Fuel consumption | 120 L | 90 L | **25% lower** |
| Throughput | 65% | 82% | **17 percentage points higher** |

These results come from the simulation configuration used in this repository. They should not be interpreted as expected performance on a deployed city road network.

## 📜 Patent

### Indian Patent Application No. 202511108091 A

A patent application has been filed for the traffic-management approach developed through this work.

[![View Patent](https://img.shields.io/badge/View%20Patent-Google%20Drive-4285F4?style=flat-square&logo=googledrive&logoColor=white)](https://drive.google.com/file/d/1QSSDN_fmPc41MEugw1atImfDk9ymtrHb/view?usp=sharing)

## 🧩 Why This Project Matters

Fixed-time traffic signals work from predefined schedules.

That becomes inefficient when traffic conditions change significantly across approaches or when emergency vehicles enter the network.

This project focuses on three connected problems:

1. **Adaptive signal control**  
   Traffic signals respond to current traffic conditions.

2. **Traffic demand forecasting**  
   LSTM forecasting is used to model changing vehicle demand.

3. **Secure controller communication**  
   Messages exchanged between traffic agents are authenticated before being trusted.

## 🏗️ System Architecture

```text
                    Historical Traffic Data
                              |
                              v
                     +------------------+
                     |  LSTM Forecast   |
                     +--------+---------+
                              |
                       Predicted Demand
                              |
                              v
                +---------------------------+
                |      SUMO Simulation      |
                |                           |
                |  J1 <-> J2 <-> J3 <-> J4 |
                |                           |
                +-------------+-------------+
                              |
                    Traffic Observations
                              |
            +-----------------+-----------------+
            |                                   |
            v                                   v
   Adaptive Signal Logic              Emergency Priority
            |                                   |
            +-----------------+-----------------+
                              |
                              v
                     Signal Decisions
                              |
                              v
              Waiting Time / Queue / Throughput
```

**SUMO** provides the traffic simulation.

**TraCI** gives the Python controllers access to vehicle states, queues and traffic lights during execution.

## 🧠 Adaptive Traffic Control

Each controlled intersection acts as an independent traffic-signal agent.

### Observed State

The controller can use information such as:

```text
queue length
waiting time
traffic density
emergency vehicle presence
```

### Actions

An agent can modify the active traffic-light phase or associated timing according to the observed state.

### Reward

The implementation penalizes congestion and accumulated waiting time.

```python
reward = -(queue_length + 0.5 * waiting_time)
```

Lower queue length and lower waiting time therefore produce a better reward.

## 📈 LSTM Traffic Forecasting

Traffic demand changes over time, so the project includes an LSTM-based forecasting component.

```text
Historical Traffic
       |
       v
   LSTM Model
       |
       v
Predicted Demand
       |
       v
Vehicle Generation
       |
       v
SUMO Simulation
       |
       v
Adaptive Control
```

The forecasting component allows experiments to use changing demand instead of one static traffic pattern.

## 🚑 Emergency Vehicle Priority

Emergency traffic is treated as a privileged case.

The controller does not trust a message only because it contains:

```json
{
  "emergency": true
}
```

A malicious sender could otherwise request priority without authorization.

Emergency requests therefore pass through the authentication and authorization layer before they influence signal behaviour.

## 🔐 Security Design

The traffic agents form a small distributed system, so the communication path is protected separately from the traffic-control algorithm.

| Threat | Example | Protection |
|---|---|---|
| Agent impersonation | Rogue process claims to be J2 | X.509 identity and certificate trust |
| Message tampering | Signal command is modified | RSA-PSS signature and SHA-256 |
| Replay | Old command is sent again | Nonce and timestamp checks |
| MITM | Traffic is intercepted or redirected | TLS 1.3 mTLS and protected metadata |
| Emergency spoofing | Normal vehicle requests priority | Signed authorization token |
| Untrusted participant | Certificate is from another CA | CA validation |

The project uses multiple layers rather than relying only on TLS.

```text
Application
Emergency Authorization

Message
RSA-PSS
SHA-256
Nonce
Timestamp
Sender / Receiver Binding

Identity
X.509 Certificates
Trusted CA

Transport
TLS 1.3
Mutual TLS
```

For the detailed security design, see [`SECURITY.md`](./SECURITY.md).

## 🧪 Security Validation

The security layer is tested independently from traffic behaviour.

Current validation includes:

- **17 automated security-focused tests**
- **6 simulated attack classes**
- TLS 1.3 mutual authentication
- X.509 identity validation
- RSA-PSS signatures
- SHA-256 integrity checks
- timestamp freshness
- nonce-based replay protection
- emergency authorization

Run:

```bash
python -m pytest -v tests/test_security.py
```

### Attack Simulation

Run:

```bash
python demo.py
```

The demo covers:

| Scenario | Expected Result |
|---|---|
| Message tampering | Blocked |
| Agent impersonation | Blocked |
| Replay | Blocked |
| MITM redirection | Blocked |
| Emergency spoofing | Blocked |
| Forged authorization token | Blocked |

### TLS Smoke Test

Run:

```bash
python tls_smoke_test.py
```

This validates the mutual TLS path independently from the signed-message tests.

## 🔧 Security Modules

| File | Purpose |
|---|---|
| `security/crypto_utils.py` | RSA, SHA-256, signing and verification |
| `security/pki.py` | certificate authority and X.509 certificates |
| `security/secure_message.py` | signed message envelopes |
| `security/secure_channel.py` | TLS 1.3 communication |
| `security/emergency_auth.py` | emergency authorization |
| `security/secure_agent.py` | integration with traffic agents |
| `security/attack_simulator.py` | adversarial scenarios |

## 🛠️ Tech Stack

| Area | Technology |
|---|---|
| Language | Python |
| Traffic Simulation | SUMO |
| Simulation Control | TraCI |
| Adaptive Control | Multi-agent traffic-control logic |
| Forecasting | LSTM |
| Numerical Computing | NumPy |
| Cryptography | RSA-2048, RSA-PSS, SHA-256 |
| Identity | X.509 PKI |
| Transport Security | TLS 1.3, mTLS |
| Testing | pytest |
| Evaluation | CSV-based simulation metrics |

## 📁 Repository Structure

```text
MARL-Driven-Real-Time-Traffic-Management-System/
|
├── marl_agent.py
├── run_marl_agent.py
├── run_secure_marl_agent.py
├── csv_gen.py
├── final2.sumocfg
|
├── fixed_timing_results.csv
├── Marl_timing_results.csv
|
├── generate_keys.py
├── demo.py
├── tls_smoke_test.py
|
├── security/
│   ├── crypto_utils.py
│   ├── pki.py
│   ├── secure_message.py
│   ├── secure_channel.py
│   ├── emergency_auth.py
│   ├── secure_agent.py
│   └── attack_simulator.py
|
├── tests/
│   └── test_security.py
|
├── SECURITY.md
├── LICENSE
└── README.md
```

## ⚙️ Running Locally

### Requirements

- Python 3.10+
- SUMO
- TraCI
- NumPy
- `cryptography`
- `pytest`

### 1. Clone the repository

```bash
git clone https://github.com/agcodes0315/MARL-Driven-Real-Time-Traffic-Management-System.git
cd MARL-Driven-Real-Time-Traffic-Management-System
```

### 2. Install Python dependencies

```bash
pip install numpy traci cryptography pytest
```

SUMO must also be installed and available in your environment.

### 3. Run the adaptive traffic simulation

```bash
python run_marl_agent.py
```

### 4. Generate agent certificates

```bash
python generate_keys.py --agents J1 J2 J3 J4
```

### 5. Run the secure simulation

```bash
python run_secure_marl_agent.py
```

### 6. Generate evaluation output

```bash
python csv_gen.py
```

### 7. Run the security tests

```bash
python -m pytest -v tests/test_security.py
```

### 8. Run the attack scenarios

```bash
python demo.py
```

### 9. Test mutual TLS

```bash
python tls_smoke_test.py
```

## 🎯 What This Project Demonstrates

This project brings together several engineering areas inside one simulation:

- adaptive traffic control
- multi-agent coordination
- LSTM forecasting
- emergency-priority logic
- secure distributed communication
- certificate-based identity
- cryptographic message validation
- adversarial testing
- simulation benchmarking

## 🤖 Google Gemini Traffic Operations Analysis

This project includes an optional **Google Gemini-powered advisory layer** that converts SUMO simulation metrics into human-readable traffic insights.

`gemini_traffic_analyzer.py` reads the generated `adaptive_demo_results.csv`, aggregates the simulation metrics locally, and uses **Gemini 3.8 Flash** to analyze:

- congestion patterns across intersections
- adaptive controller behaviour
- intersections requiring attention
- areas for further investigation

The generated analysis is saved as `gemini_traffic_analysis.md`.

### Run

Install the Google GenAI SDK:

```bash
python -m pip install -U google-genai
```

Set your Gemini API key:

```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
```

Run the analyzer:

```bash
python gemini_traffic_analyzer.py
```

### Flow

```text
SUMO Simulation
      ↓
Adaptive Traffic Control
      ↓
Simulation Metrics
      ↓
Google Gemini 3.8 Flash
      ↓
Traffic Operations Analysis
      ↓
Human Operator / Researcher
```

> **Safety:** Gemini is advisory only. It does not control traffic signals or modify signal phases. The analysis is based on SUMO simulation data, not live municipal traffic data.

## ⚠️ Scope and Limitations

This repository is a **simulation and research project**.

The traffic results come from SUMO and do not represent deployment results from a real municipal traffic network.

The security implementation is also a prototype and is not a certified Intelligent Transportation System security platform.

Current limitations include:

- simulation-scale road networks
- no live municipal sensor feed
- no production certificate revocation service
- no hardware-backed key storage
- no large-scale DoS mitigation
- no compromised-controller recovery
- no post-quantum cryptography

## 🔭 Possible Next Steps

- larger SUMO road networks
- cooperative traffic-agent policies
- additional baseline comparisons
- real traffic sensor datasets
- camera-based vehicle detection
- edge deployment
- certificate rotation and revocation
- controller attestation
- Byzantine-agent detection
- security telemetry
- post-quantum authentication experiments

## 📚 Project Resources

| Resource | Link |
|---|---|
| Repository | [GitHub](https://github.com/agcodes0315/MARL-Driven-Real-Time-Traffic-Management-System) |
| Patent | [View document](https://drive.google.com/file/d/1QSSDN_fmPc41MEugw1atImfDk9ymtrHb/view?usp=sharing) |
| Security Documentation | [`SECURITY.md`](./SECURITY.md) |
| Security Tests | [`tests/test_security.py`](./tests/test_security.py) |

## 👩‍💻 Author

### Agrima Saxena

**Software Engineering · Applied AI · Secure Systems**

<table>
<tr>

<td width="60">
<a href="https://www.linkedin.com/in/agrima-saxena-142960426/" title="LinkedIn">
<img src="https://img.icons8.com/color/48/linkedin.png"
     width="32"
     height="32"
     alt="LinkedIn"/>
</a>
</td>

<td width="60">
<a href="mailto:agrimalc@gmail.com" title="Email">
<img src="https://img.icons8.com/color/48/gmail-new.png"
     width="32"
     height="32"
     alt="Email"/>
</a>
</td>

<td width="60">
<a href="https://github.com/agcodes0315" title="GitHub">
<img src="https://img.icons8.com/ios-glyphs/48/ffffff/github.png"
     width="32"
     height="32"
     alt="GitHub"/>
</a>
</td>

</tr>
</table>

<a href="https://github.com/agcodes0315/MARL-Driven-Real-Time-Traffic-Management-System">
<img src="https://img.shields.io/badge/GitHub-View%20Repository-181717?style=flat-square&logo=github&logoColor=white"
     alt="MARL Repository"/>
</a>

<a href="https://drive.google.com/file/d/1QSSDN_fmPc41MEugw1atImfDk9ymtrHb/view?usp=sharing">
<img src="https://img.shields.io/badge/View-Patent-4285F4?style=flat-square&logo=googledrive&logoColor=white"
     alt="View Patent"/>
</a>

<br><br>

⭐ **If you found the project useful or the architecture interesting, consider starring the repository.**