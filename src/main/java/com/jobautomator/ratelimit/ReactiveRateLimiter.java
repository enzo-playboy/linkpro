package com.jobautomator.ratelimit;

import com.jobautomator.exception.RateLimitExceededException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicReference;

/**
 * High-performance, non-blocking Token Bucket Reactive Rate Limiter.
 * Uses atomic CAS operations and Project Reactor's non-blocking Mono.delay
 * to throttle operations safely without blocking any thread.
 */
public class ReactiveRateLimiter {
    private static final Logger log = LoggerFactory.getLogger(ReactiveRateLimiter.class);

    private final Map<String, TokenBucket> buckets = new ConcurrentHashMap<>();

    public ReactiveRateLimiter() {
        // Register default rate limit configs for known services
        registerService(ServiceName.LINKEDIN_SCRAPING, RateLimitConfig.linkedInScrapingDefault());
        registerService(ServiceName.BROWSERGYM_APPLY, RateLimitConfig.browserGymApplyDefault());
        registerService(ServiceName.OPENAI_API, RateLimitConfig.openAiDefault());
        registerService(ServiceName.GMAIL_MONITOR, RateLimitConfig.gmailMonitorDefault());
    }

    public void registerService(String serviceName, RateLimitConfig config) {
        buckets.put(serviceName, new TokenBucket(config));
    }

    /**
     * Non-blockingly acquires a token for the given service.
     * If capacity is depleted, delays execution reactively without blocking any thread.
     *
     * @param serviceName Service to throttle
     * @return Mono completing when a token has been acquired
     */
    public Mono<Void> acquire(String serviceName) {
        TokenBucket bucket = buckets.computeIfAbsent(serviceName,
                k -> new TokenBucket(RateLimitConfig.of(10, Duration.ofSeconds(60))));

        return Mono.defer(() -> {
            long waitNanos = bucket.tryConsumeOrGetWaitNanos();
            if (waitNanos <= 0) {
                return Mono.empty();
            }

            Duration delay = Duration.ofNanos(waitNanos);
            log.debug("[ReactiveRateLimiter] Rate limit reached for '{}'. Non-blocking delay of {} ms",
                    serviceName, delay.toMillis());

            return Mono.delay(delay).then(acquire(serviceName));
        });
    }

    /**
     * Attempts to acquire a token immediately without waiting.
     *
     * @param serviceName Service to check
     * @return Mono emitting true if acquired, or false if limit is reached
     */
    public Mono<Boolean> tryAcquire(String serviceName) {
        TokenBucket bucket = buckets.computeIfAbsent(serviceName,
                k -> new TokenBucket(RateLimitConfig.of(10, Duration.ofSeconds(60))));

        return Mono.fromCallable(() -> {
            long waitNanos = bucket.tryConsumeOrGetWaitNanos();
            return waitNanos <= 0;
        });
    }

    /**
     * Executes the supplied reactive publisher only after acquiring a rate limit token.
     */
    public <T> Mono<T> throttle(String serviceName, Mono<T> publisher) {
        return acquire(serviceName).then(publisher);
    }

    /**
     * Internal atomic token bucket representation.
     */
    private static class TokenBucket {
        private final int maxTokens;
        private final long refillPeriodNanos;
        private final double refillTokensPerNano;
        private final AtomicReference<State> stateRef;

        private record State(double availableTokens, long lastRefillNanos) {}

        TokenBucket(RateLimitConfig config) {
            this.maxTokens = config.maxTokens();
            this.refillPeriodNanos = config.refillPeriod().toNanos();
            this.refillTokensPerNano = (double) maxTokens / (double) refillPeriodNanos;
            this.stateRef = new AtomicReference<>(new State(maxTokens, System.nanoTime()));
        }

        /**
         * @return 0 if token was consumed successfully, or positive nanoseconds until next token is available.
         */
        long tryConsumeOrGetWaitNanos() {
            while (true) {
                State current = stateRef.get();
                long now = System.nanoTime();
                long elapsed = Math.max(0, now - current.lastRefillNanos());

                // Calculate refilled tokens capped at maxTokens
                double refilled = Math.min(maxTokens, current.availableTokens() + (elapsed * refillTokensPerNano));

                if (refilled >= 1.0) {
                    State next = new State(refilled - 1.0, now);
                    if (stateRef.compareAndSet(current, next)) {
                        return 0; // Success
                    }
                } else {
                    // Tokens not available yet, calculate wait duration for 1 token
                    double needed = 1.0 - refilled;
                    long waitNanos = (long) Math.ceil(needed / refillTokensPerNano);
                    return Math.max(1, waitNanos);
                }
            }
        }
    }
}
