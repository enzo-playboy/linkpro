package com.jobautomator.security;

/**
 * Encapsulates the execution result of an external sub-process.
 */
public record ProcessExecutionResult(
        int exitCode,
        String stdout,
        String stderr,
        long executionDurationMillis
) {
    public boolean isSuccess() {
        return exitCode == 0;
    }
}
