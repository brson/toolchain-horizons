# Removing the `futures` Dependency

## Step 1: Break out sub-crates (`f7cc94b53`)
Replace monolithic `futures` with specific sub-crates to identify exact functionality needed.

### Option A: Before/after Cargo.toml
```toml
# Before
[dependencies]
futures = "0.3.31"

# After
[dependencies]
futures-channel = "0.3.31"

[dev-dependencies]
futures-executor = "0.3.31"
futures-util = "0.3.31"
```

### Option B: Just the description
"Split `futures` into sub-crates to isolate what we actually use: channels (runtime), executor + utils (dev only)"


> me: Option A

---

## Step 2: Polyfill `block_on` (`abd5b9774`)
Remove `futures-executor` by implementing minimal async executor.

### Option A: Full implementation
```rust
pub fn block_on<F: Future>(future: F) -> F::Output {
    let mut future = Box::pin(future);
    let parker = Arc::new(Parker::new());
    let waker = parker_into_waker(parker.clone());
    let mut context = Context::from_waker(&waker);

    loop {
        match future.as_mut().poll(&mut context) {
            Poll::Ready(result) => return result,
            Poll::Pending => parker.park(),
        }
    }
}
```

### Option B: Unsafe/scary parts
```rust
const VTABLE: RawWakerVTable = RawWakerVTable::new(
    clone, wake, wake_by_ref, drop
);

unsafe fn clone(ptr: *const ()) -> RawWaker {
    let parker = Arc::from_raw(ptr as *const Parker);
    let cloned = parker.clone();
    let _ = Arc::into_raw(parker);
    parker_into_raw_waker(cloned)
}

unsafe fn wake(ptr: *const ()) {
    let parker = Arc::from_raw(ptr as *const Parker);
    parker.unpark();
}
```

### Option C: Before/after contrast
```rust
// Before: 1 line
futures::executor::block_on(my_future)

// After: 88 lines including:
// - Parker struct with Mutex<bool> + Condvar
// - RawWakerVTable with 4 unsafe functions
// - Manual Arc reference counting
```

### Option D: Type signatures + line count
```rust
pub fn block_on<F: Future>(future: F) -> F::Output { /* 12 lines */ }
struct Parker { /* 20 lines */ }
const VTABLE: RawWakerVTable = /* 4 unsafe fns, 30 lines */
fn parker_into_waker(parker: Arc<Parker>) -> Waker { /* 8 lines */ }
```

> me: Option C, with speakernotes about the gnarliness of the waker


---

## Step 3: Polyfill Stream utilities (`632b5ed6d`)
Remove `futures-util` by reimplementing Stream abstractions.

### Option A: Full Stream trait
```rust
pub trait Stream {
    type Item;
    fn poll_next(self: Pin<&mut Self>, cx: &mut Context<'_>)
        -> Poll<Option<Self::Item>>;
}

pub trait StreamExt: Stream {
    fn next(&mut self) -> Next<'_, Self>
    where Self: Unpin
    {
        Next { stream: self }
    }
}
```

### Option B: The unfold implementation (complex part)
```rust
impl<T, F, Fut, Item> Stream for Unfold<T, F, Fut>
where
    F: FnMut(T) -> Fut,
    Fut: Future<Output = Option<(Item, T)>>,
{
    type Item = Item;

    fn poll_next(self: Pin<&mut Self>, cx: &mut Context<'_>)
        -> Poll<Option<Self::Item>>
    {
        // SAFETY: We never move out of the pinned fields.
        let this = unsafe { self.get_unchecked_mut() };
        // ... 25 more lines of state machine
    }
}
```

### Option C: Before/after contrast
```rust
// Before: use futures_util
use futures_util::{stream, StreamExt};
stream::unfold(0, |state| async { Some((state, state + 1)) })

// After: 120 lines including:
// - Stream trait definition
// - StreamExt trait with next()
// - Next future type
// - unfold() function
// - Unfold struct with manual poll_next state machine
// - pin_mut! macro
```

### Option D: List of what we had to reimplement
```rust
// Reimplemented from futures-util:
pub trait Stream { ... }           // 8 lines
pub trait StreamExt { ... }        // 12 lines
pub struct Next<'a, S> { ... }     // 15 lines
pub fn unfold<T, F, Fut, Item>     // 45 lines
pub struct Unfold<T, F, Fut>       // 35 lines
macro_rules! pin_mut! { ... }      // 10 lines
```

> me: Option D

---

## Step 4: Polyfill oneshot channel (`381de6c81`)
Remove `futures-channel` - final runtime dependency!

### Option A: Full implementation
```rust
struct OneshotFuture<T> {
    shared: Arc<OneshotShared<T>>,
}

struct OneshotShared<T> {
    waker: Mutex<Option<Waker>>,
    value: Mutex<Option<T>>,
}

impl<T> Future for OneshotFuture<T> {
    type Output = T;

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        let mut value = self.shared.value.lock().unwrap();
        if let Some(val) = value.take() {
            return Poll::Ready(val);
        }
        let mut waker = self.shared.waker.lock().unwrap();
        *waker = Some(cx.waker().clone());
        Poll::Pending
    }
}

impl<T> OneshotSender<T> {
    fn send(self, value: T) {
        let mut val_guard = self.shared.value.lock().unwrap();
        *val_guard = Some(value);
        drop(val_guard);

        let mut waker = self.shared.waker.lock().unwrap();
        if let Some(waker) = waker.take() {
            waker.wake();
        }
    }
}
```

### Option B: Before/after contrast
```rust
// Before: 1 line
let (tx, rx) = futures_channel::oneshot::channel();

// After: 60 lines including:
// - OneshotFuture<T> struct
// - OneshotShared<T> with two Mutexes
// - OneshotSender<T> struct
// - Future impl with Waker management
// - Manual Arc sharing between sender/receiver
```

### Option C: Type signatures only
```rust
struct OneshotFuture<T> { shared: Arc<OneshotShared<T>> }
struct OneshotShared<T> { waker: Mutex<Option<Waker>>, value: Mutex<Option<T>> }
struct OneshotSender<T> { shared: Arc<OneshotShared<T>> }

impl<T> Future for OneshotFuture<T> { /* 12 lines */ }
impl<T> OneshotSender<T> { fn send(self, value: T) { /* 10 lines */ } }
```

> me: Option C

---

## Summary Slide Options

### Option A: Line count impact
```
futures crate removed: -1 dependency
polyfill code added:   +270 lines
  - block_on:      88 lines
  - Stream utils: 120 lines
  - oneshot:       60 lines
```

### Option B: Visual before/after
```
Before                          After
------                          -----
futures = "0.3.31"              futures_polyfills.rs (210 lines)
                                + inline oneshot (60 lines)
                                + 4 unsafe functions
                                + manual Waker management
```
