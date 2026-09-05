// Active-session counting. Reads a problem from stdin, writes one count per query
// to stdout. See TASK.md for the format and semantics.
//
// NAIVE STARTER — O(N*Q): for each query it scans every session. Correct on small
// inputs but far too slow for the large performance case. Make it fast enough.
use std::io::{self, Read, Write};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut it = input.split_ascii_whitespace().map(|x| x.parse::<i64>().unwrap());

    let n = it.next().unwrap() as usize;
    let mut sessions: Vec<(i64, i64)> = Vec::with_capacity(n);
    for _ in 0..n {
        let s = it.next().unwrap();
        let e = it.next().unwrap();
        sessions.push((s, e));
    }
    let q = it.next().unwrap() as usize;

    let mut out = String::new();
    for _ in 0..q {
        let t = it.next().unwrap();
        // O(N) scan per query.
        let mut count: u64 = 0;
        for &(s, e) in &sessions {
            if s <= t && t <= e {
                count += 1;
            }
        }
        out.push_str(&count.to_string());
        out.push('\n');
    }
    io::stdout().write_all(out.as_bytes()).unwrap();
}
