use axum::http::HeaderValue;
fn main() {
    let s = "not a valid origin";
    match s.parse::<HeaderValue>() {
        Ok(v) => println!("Parsed: {:?}", v),
        Err(e) => println!("Error: {:?}", e),
    }
}
