package com.jobautomator.exception;

/**
 * Thrown when an agent or service exceeds configured rate limits or throughput thresholds.
 */
public class RateLimitExceededException extends JobAutomatorException {
    private final String serviceName;
    private final long retryAfterMillis;

    public RateLimitExceededException(String serviceName, long retryAfterMillis) {
        super(String.format("Rate limit exceeded for service '%s'. Retry after %d ms.", serviceName, retryAfterMillis));
        this.serviceName = serviceName;
        this.retryAfterMillis = retryAfterMillis;
    }

    public String getServiceName() {
        return serviceName;
    }

    public long getRetryAfterMillis() {
        return retryAfterMillis;
    }
}
