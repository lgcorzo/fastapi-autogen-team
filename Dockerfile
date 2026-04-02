# Build stage
FROM rust:1.80-slim-bookworm AS builder

# Create a dummy project to cache dependencies
WORKDIR /usr/src/app
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release
RUN rm -f target/release/deps/fastapi_autogen_team*

# Copy the actual source and build
COPY . .
RUN cargo build --release

# Runtime stage
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/bin
COPY --from=builder /usr/src/app/target/release/fastapi-autogen-team .

# Expose the Axum port
EXPOSE 8000

# Set environment variables for Rig/Axum
ENV RUST_LOG=info

CMD ["./fastapi-autogen-team"]