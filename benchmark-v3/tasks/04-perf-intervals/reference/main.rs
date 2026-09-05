// Reference: sort starts and ends, answer each query by binary search.
// active(t) = (#starts <= t) - (#ends < t), O((N+Q) log N).
use std::io::{self, Read, Write};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut it = input.split_ascii_whitespace().map(|x| x.parse::<i64>().unwrap());

    let n = it.next().unwrap() as usize;
    let mut starts: Vec<i64> = Vec::with_capacity(n);
    let mut ends: Vec<i64> = Vec::with_capacity(n);
    for _ in 0..n {
        starts.push(it.next().unwrap());
        ends.push(it.next().unwrap());
    }
    starts.sort_unstable();
    ends.sort_unstable();

    let q = it.next().unwrap() as usize;
    let mut out = String::with_capacity(q * 3);
    for _ in 0..q {
        let t = it.next().unwrap();
        // #starts <= t  == partition_point(|&x| x <= t)
        let a = starts.partition_point(|&x| x <= t) as u64;
        // #ends < t     == partition_point(|&x| x < t)
        let b = ends.partition_point(|&x| x < t) as u64;
        out.push_str(&(a - b).to_string());
        out.push('\n');
    }
    io::stdout().write_all(out.as_bytes()).unwrap();
}
