# Module Architecture

The following diagram represents the core module structure of the migrated Rust service.

![Module Hierarchy](architecture_modules.plantuml)

---

## 🛠️ Main Components

- **main.rs**: Bootstraps the Axum server and environment configuration.
- **lib.rs**: Defines the `create_app` router and the `AppState` struct.
- **agents.rs**: The orchestration core using the **Rig** framework.
- **tools.rs**: Concrete implementations of the Tool trait for Jira and R2R.
- **data_model.rs**: Serde-enabled structs for API communication.
