package com.jobautomator.exception;

/**
 * Thrown when an input, path, command, or parameter fails security validation.
 */
public class SecurityValidationException extends JobAutomatorException {
    private final String violationDetail;

    public SecurityValidationException(String message) {
        super(message);
        this.violationDetail = message;
    }

    public SecurityValidationException(String message, String violationDetail) {
        super(message);
        this.violationDetail = violationDetail;
    }

    public String getViolationDetail() {
        return violationDetail;
    }
}
