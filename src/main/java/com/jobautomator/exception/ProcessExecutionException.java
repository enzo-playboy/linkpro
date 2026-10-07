package com.jobautomator.exception;

/**
 * Thrown when an external process fails to execute, times out, or returns a non-zero exit code.
 */
public class ProcessExecutionException extends JobAutomatorException {
    private final int exitCode;
    private final String stderr;

    public ProcessExecutionException(String message) {
        super(message);
        this.exitCode = -1;
        this.stderr = "";
    }

    public ProcessExecutionException(String message, Throwable cause) {
        super(message, cause);
        this.exitCode = -1;
        this.stderr = "";
    }

    public ProcessExecutionException(String message, int exitCode, String stderr) {
        super(String.format("%s (exitCode=%d, stderr=%s)", message, exitCode, stderr));
        this.exitCode = exitCode;
        this.stderr = stderr;
    }

    public int getExitCode() {
        return exitCode;
    }

    public String getStderr() {
        return stderr;
    }
}
