package com.jobautomator.exception;

/**
 * Base unchecked exception for all JobAutomator errors.
 */
public class JobAutomatorException extends RuntimeException {
    public JobAutomatorException(String message) {
        super(message);
    }

    public JobAutomatorException(String message, Throwable cause) {
        super(message, cause);
    }
}
