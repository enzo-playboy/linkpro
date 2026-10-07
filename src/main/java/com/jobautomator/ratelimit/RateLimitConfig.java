package com.jobautomator.ratelimit;

import java.time.Duration;

/**
 * Configuration for token-bucket rate limiting on external APIs and services.
 */
public record RateLimitConfig(
        int maxTokens,
        Duration refillPeriod
) {
    public static RateLimitConfig of(int maxTokens, Duration refillPeriod) {
        if (maxTokens <= 0) {
            throw new IllegalArgumentException("maxTokens must be greater than 0");
        }
        if (refillPeriod == null || refillPeriod.isZero() || refillPeriod.isNegative()) {
            throw new IllegalArgumentException("refillPeriod must be positive");
        }
        return new RateLimitConfig(maxTokens, refillPeriod);
    }

    /**
     * LinkedIn Scraping: safe pace (e.g. 5 requests per 30 seconds).
     */
    public static RateLimitConfig linkedInScrapingDefault() {
        return RateLimitConfig.of(5, Duration.ofSeconds(30));
    }

    /**
     * BrowserGym Auto-Apply: conservative pacing (e.g. 2 applications per 60 seconds) to avoid detection.
     */
    public static RateLimitConfig browserGymApplyDefault() {
        return RateLimitConfig.of(2, Duration.ofSeconds(60));
    }

    /**
     * OpenAI API: default allowance (e.g. 30 requests per minute).
     */
    public static RateLimitConfig openAiDefault() {
        return RateLimitConfig.of(30, Duration.ofSeconds(60));
    }

    /**
     * Gmail Monitor: periodic scans (e.g. 10 requests per minute).
     */
    public static RateLimitConfig gmailMonitorDefault() {
        return RateLimitConfig.of(10, Duration.ofSeconds(60));
    }
}
