use clap::{Parser, ValueEnum};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(name = "crash-generator")]
#[command(about = "Generate various types of crashes for testing minidump analysis")]
struct Args {
    #[arg(value_enum)]
    crash_type: CrashType,
    
    #[arg(short, long, default_value = "./crash.dmp")]
    output: PathBuf,
    
    #[arg(short, long)]
    generate_dump: bool,
}

#[derive(Copy, Clone, Debug, PartialEq, Eq, PartialOrd, Ord, ValueEnum)]
enum CrashType {
    Null,
    StackOverflow,
    DivideByZero,
    Assert,
    Panic,
    Segfault,
}

fn main() {
    let args = Args::parse();
    
    if args.generate_dump {
        setup_crash_handler(&args.output);
    }
    
    println!("Generating {:?} crash...", args.crash_type);
    
    match args.crash_type {
        CrashType::Null => cause_null_deref(),
        CrashType::StackOverflow => cause_stack_overflow(),
        CrashType::DivideByZero => cause_divide_by_zero(),
        CrashType::Assert => cause_assert_failure(),
        CrashType::Panic => cause_panic(),
        CrashType::Segfault => cause_segfault(),
    }
}

fn setup_crash_handler(output_path: &PathBuf) {
    println!("Setting up crash handler for output: {:?}", output_path);
    
    #[cfg(unix)]
    {
        use std::sync::Mutex;
        static OUTPUT_PATH: Mutex<Option<PathBuf>> = Mutex::new(None);
        
        *OUTPUT_PATH.lock().unwrap() = Some(output_path.clone());
        
        unsafe {
            libc::signal(libc::SIGSEGV, handle_crash_unix as usize);
            libc::signal(libc::SIGABRT, handle_crash_unix as usize);
            libc::signal(libc::SIGFPE, handle_crash_unix as usize);
        }
        
        extern "C" fn handle_crash_unix(sig: i32) {
            eprintln!("Caught signal: {}", sig);
            if let Ok(path) = OUTPUT_PATH.lock() {
                if let Some(output) = path.as_ref() {
                    eprintln!("Writing minidump to: {:?}", output);
                    #[cfg(target_os = "linux")]
                    {
                        let result = minidump_writer::minidump_writer::MinidumpWriter::new(
                            std::process::id() as i32,
                            std::process::id() as i32,
                        ).dump(output.as_path());
                        match result {
                            Ok(_) => eprintln!("Minidump write result: Ok"),
                            Err(e) => eprintln!("Minidump write result: Err({})", e),
                        }
                    }
                    #[cfg(target_os = "macos")]
                    {
                        use std::fs::File;
                        match File::create(output) {
                            Ok(mut file) => {
                                let result = minidump_writer::minidump_writer::MinidumpWriter::new(
                                    None,
                                    None,
                                ).dump(&mut file);
                                match result {
                                    Ok(_) => eprintln!("Minidump write result: Ok"),
                                    Err(e) => eprintln!("Minidump write result: Err({})", e),
                                }
                            }
                            Err(e) => eprintln!("Failed to create file: {}", e),
                        }
                    }
                }
            }
            std::process::exit(1);
        }
    }
    
    #[cfg(windows)]
    {
        use windows::Win32::System::Diagnostics::Debug::*;
        use std::ptr;
        
        unsafe {
            SetUnhandledExceptionFilter(Some(handle_crash_windows));
        }
        
        unsafe extern "system" fn handle_crash_windows(
            _exception_info: *mut EXCEPTION_POINTERS
        ) -> i32 {
            // Windows minidump implementation would go here
            // For now, just exit
            EXCEPTION_EXECUTE_HANDLER
        }
    }
}

#[inline(never)]
fn cause_null_deref() {
    println!("About to cause null pointer dereference...");
    unsafe {
        let p: *const i32 = std::ptr::null();
        println!("Reading from null pointer...");
        std::ptr::write_volatile(p as *mut i32, 42);
        println!("This should never print");
    }
}

#[inline(never)]
fn cause_stack_overflow() {
    let _arr = [0u8; 1_000_000];
    #[allow(unconditional_recursion)]
    cause_stack_overflow();
}

#[inline(never)]
fn cause_divide_by_zero() {
    unsafe {
        let a: i32 = 42;
        let mut b: i32 = 1;
        std::ptr::write_volatile(&mut b as *mut i32, 0);
        let _c = a / b;
    }
}

#[inline(never)]
fn cause_assert_failure() {
    assert!(false, "This assertion always fails");
}

#[inline(never)]
fn cause_panic() {
    panic!("Intentional panic for testing");
}

#[inline(never)]
fn cause_segfault() {
    unsafe {
        let ptr = 0x1 as *mut i32;
        *ptr = 42;
    }
}