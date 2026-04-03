# Build stage
FROM rust:latest AS builder

# Create a dummy project to cache dependencies
WORKDIR /usr/src/app
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && touch src/lib.rs && echo "fn main() {}" > src/main.rs
RUN cargo build --release
RUN rm -f target/release/deps/fastapi_autogen_team*

# Copy the actual source and build
COPY . .
RUN touch src/lib.rs && cargo build --release

# Runtime stage
FROM debian:trixie-slim

RUN apt-get update && apt-get install -y \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/bin
COPY --from=builder /usr/src/app/target/release/fastapi-autogen-team .

# Expose the Axum port
EXPOSE 4100

# Set environment variables for Rig/Axum
ENV RUST_LOG=info
ENV DEFAULT_PORT=4100

CMD ["./fastapi-autogen-team"]