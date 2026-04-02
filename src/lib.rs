pub mod application;
pub mod domain;
pub mod infrastructure;
pub mod interface;

// For backward compatibility during migration or as entry points
pub use interface::http::routes::{create_app, AppState};
